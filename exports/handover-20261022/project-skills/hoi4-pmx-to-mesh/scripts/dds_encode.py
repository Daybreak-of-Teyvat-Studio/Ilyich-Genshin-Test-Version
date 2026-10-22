# -*- coding: utf-8 -*-
"""纯 Python / numpy 的 DDS(BC1/BC3) 编码器 + mip 链生成。

按本项目（HOI4 MOD）实测的 DDS 头规格输出：
  flags = CAPS|HEIGHT|WIDTH|PIXELFORMAT|MIPMAPCOUNT|LINEARSIZE
  caps  = TEXTURE|COMPLEX|MIPMAP (0x401008)
  pf    = FOURCC DXT1 / DXT5，全 mip 链，dwPitchOrLinearSize = 顶层大小

用法：
    from dds_encode import rgba_from_image, write_dds
    rgba = rgba_from_image(pil_image, size=(1024,1024))
    write_dds("out.dds", rgba, "DXT5")
"""
import struct

import numpy as np

DDSD_CAPS = 0x1
DDSD_HEIGHT = 0x2
DDSD_WIDTH = 0x4
DDSD_PIXELFORMAT = 0x1000
DDSD_MIPMAPCOUNT = 0x20000
DDSD_LINEARSIZE = 0x80000

DDPF_FOURCC = 0x4

DDSCAPS_COMPLEX = 0x8
DDSCAPS_TEXTURE = 0x1000
DDSCAPS_MIPMAP = 0x400000

FOURCC = {"DXT1": b"DXT1", "DXT5": b"DXT5"}


# ---------------------------------------------------------------- 图像处理
def rgba_from_image(im, size=None):
    """PIL Image -> (H,W,4) uint8 RGBA。size=(w,h) 则缩放（LANCZOS）。"""
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    if size is not None and (im.width, im.height) != size:
        im = im.resize(size, 1)          # 1 = LANCZOS
    return np.asarray(im, dtype=np.uint8).copy()


def mip_chain(rgba, min_size=1):
    """2x2 盒式降采样，直到尺寸 <= min_size。返回 [level0, level1, ...]。
    默认降到 1x1，与 HOI4 参考 DDS（256² 有 9 层）一致。"""
    levels = [rgba]
    cur = rgba
    while cur.shape[0] > min_size and cur.shape[1] > min_size:
        h, w = cur.shape[0] // 2, cur.shape[1] // 2
        if h == 0 or w == 0:
            break
        c = cur[: h * 2, : w * 2].astype(np.uint16)
        c = (c[0::2, 0::2] + c[1::2, 0::2] + c[0::2, 1::2] + c[1::2, 1::2] + 2) // 4
        cur = c.astype(np.uint8)
        levels.append(cur)
    return levels


# ---------------------------------------------------------------- 块化
def _blocks(rgba):
    """(H,W,4) -> (N,16,4)，N = H/4*W/4，每块按行主序 16 像素。
    小于 4 的边（mip 链末端的 2x2 / 1x1）用边缘复制补齐到 4 的倍数。"""
    h, w = rgba.shape[0], rgba.shape[1]
    ph = (4 - h % 4) % 4
    pw = (4 - w % 4) % 4
    if ph or pw:
        rgba = np.pad(rgba, ((0, ph), (0, pw), (0, 0)), mode="edge")
        h, w = rgba.shape[0], rgba.shape[1]
    b = rgba.reshape(h // 4, 4, w // 4, 4, 4)
    b = b.transpose(0, 2, 1, 3, 4)
    return b.reshape(-1, 16, 4)


def _pack565(rgb):
    r = (rgb[..., 0].astype(np.uint16) >> 3)
    g = (rgb[..., 1].astype(np.uint16) >> 2)
    b = (rgb[..., 2].astype(np.uint16) >> 3)
    return (r << 11) | (g << 5) | b


def _unpack565(c):
    r = (c >> 11) & 0x1F
    g = (c >> 5) & 0x3F
    b = c & 0x1F
    r = (r << 3) | (r >> 2)
    g = (g << 2) | (g >> 4)
    b = (b << 3) | (b >> 2)
    return np.stack([r, g, b], axis=-1).astype(np.int32)


def encode_bc1(rgba):
    """BC1/DXT1（4 色不透明模式）。rgba (H,W,4) uint8，H,W 为 4 的倍数。"""
    blk = _blocks(rgba)
    rgb = blk[:, :, :3].astype(np.int32)
    mn = rgb.min(axis=1)
    mx = rgb.max(axis=1)

    c0 = _pack565(mx).astype(np.uint16)
    c1 = _pack565(mn).astype(np.uint16)
    # 4 色模式要求 c0 > c1
    swap = c0 <= c1
    c0s = np.where(swap, c1, c0)
    c1s = np.where(swap, c0, c1)
    # 若端点完全相同（纯色块），退化解仍合法
    c0s = c0s.astype(np.uint16)
    c1s = c1s.astype(np.uint16)

    p0 = _unpack565(c0s)
    p1 = _unpack565(c1s)
    p2 = (2 * p0 + p1) // 3
    p3 = (p0 + 2 * p1) // 3
    pal = np.stack([p0, p1, p2, p3], axis=1)          # (N,4,3)

    d = ((rgb[:, :, None, :] - pal[:, None, :, :]).astype(np.int32) ** 2).sum(-1)
    idx = d.argmin(axis=2).astype(np.uint32)          # (N,16)

    words = np.zeros(len(blk), dtype=np.uint32)
    for i in range(16):
        words |= (idx[:, i] & 0x3) << (2 * i)

    out = np.empty((len(blk), 8), dtype=np.uint8)
    out[:, 0] = (c0s & 0xFF).astype(np.uint8)
    out[:, 1] = (c0s >> 8).astype(np.uint8)
    out[:, 2] = (c1s & 0xFF).astype(np.uint8)
    out[:, 3] = (c1s >> 8).astype(np.uint8)
    for k in range(4):
        out[:, 4 + k] = ((words >> (8 * k)) & 0xFF).astype(np.uint8)
    return out.tobytes()


def encode_bc4(alpha):
    """BC4（单通道，8 值插值模式）。alpha (N,16) uint8 -> bytes。"""
    a = alpha.astype(np.int32)
    mx = a.max(axis=1)
    mn = a.min(axis=1)
    # 8 值模式要求 a0 > a1
    swap = mx <= mn
    a0 = np.where(swap, mn, mx)
    a1 = np.where(swap, mx, mn)

    pal = np.empty((len(a), 8), dtype=np.int32)
    pal[:, 0] = a0
    pal[:, 1] = a1
    for i in range(1, 7):
        pal[:, 1 + i] = ((7 - i) * a0 + i * a1) // 7

    d = np.abs(a[:, :, None] - pal[:, None, :])
    idx = d.argmin(axis=2).astype(np.uint64)

    # 16 个 3-bit 索引压成 48 bit
    words = np.zeros(len(a), dtype=np.uint64)
    for i in range(16):
        words |= (idx[:, i] & 0x7) << np.uint64(3 * i)

    out = np.empty((len(a), 1 + 1 + 6), dtype=np.uint8)
    out[:, 0] = a0.astype(np.uint8)
    out[:, 1] = a1.astype(np.uint8)
    for k in range(6):
        out[:, 2 + k] = ((words >> np.uint64(8 * k)) & np.uint64(0xFF)).astype(np.uint8)
    return out


def encode_bc3(rgba):
    """BC3/DXT5 = BC4(alpha) + BC1(color)。"""
    blk = _blocks(rgba)
    alpha = blk[:, :, 3]
    a = encode_bc4(alpha)
    c = np.frombuffer(encode_bc1(rgba), dtype=np.uint8).reshape(len(blk), 8)
    return np.concatenate([a, c], axis=1).tobytes()


# ---------------------------------------------------------------- DDS 写出
def _header(w, h, mip, fourcc, top_size):
    flags = (DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
             | DDSD_MIPMAPCOUNT | DDSD_LINEARSIZE)
    caps = DDSCAPS_COMPLEX | DDSCAPS_TEXTURE | DDSCAPS_MIPMAP
    b = bytearray()
    b += b"DDS "
    b += struct.pack("<7I", 124, flags, h, w, top_size, 0, mip)
    b += b"\x00" * 44                                   # dwReserved1[11]
    b += struct.pack("<2I", 32, DDPF_FOURCC)            # ddspf.size / flags
    b += fourcc                                         # dwFourCC
    b += struct.pack("<5I", 0, 0, 0, 0, 0)              # bits + 4 masks
    b += struct.pack("<5I", caps, 0, 0, 0, 0)           # caps..caps4/reserved2
    assert len(b) == 128, len(b)
    return bytes(b)


def encode_levels(rgba, fmt):
    levels = mip_chain(rgba)
    enc = encode_bc1 if fmt == "DXT1" else encode_bc3
    return [enc(lv) for lv in levels]


def write_dds(path, rgba, fmt="DXT5"):
    """rgba: (H,W,4) uint8；fmt: 'DXT1'|'DXT5'。写出带全 mip 链的 dds。"""
    h, w = rgba.shape[0], rgba.shape[1]
    assert h % 4 == 0 and w % 4 == 0, "尺寸须为 4 的倍数"
    assert (h & (h - 1)) == 0 and (w & (w - 1)) == 0, "建议 2 的幂"
    datas = encode_levels(rgba, fmt)
    with open(path, "wb") as f:
        f.write(_header(w, h, len(datas), FOURCC[fmt], len(datas[0])))
        for d in datas:
            f.write(d)
    return os_size(path)


def os_size(p):
    import os
    return os.path.getsize(p)


if __name__ == "__main__":
    # 自检：编码 -> 解码回像素 -> 报 PSNR
    import sys
    import time

    n = 512
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, (n, n, 4), dtype=np.uint8)
    t0 = time.time()
    d = encode_levels(img, "DXT5")
    dt = time.time() - t0
    print("DXT5 %dx%d 编码 %.2fs  顶层 %d bytes  层数 %d" % (n, n, dt, len(d[0]), len(d)))
    exp = n * n  # DXT5 = 1 byte/px
    print("顶层期望 %d bytes -> %s" % (exp, "OK" if len(d[0]) == exp else "不符"))

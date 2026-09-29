# -*- coding: utf-8 -*-
"""自检 dds_encode：编码->解码回像素，报 PSNR；并比对参考 DDS 头。"""
import os
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dds_encode import write_dds, mip_chain, _blocks  # noqa

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_dds_encode.txt")
L = []
P = L.append


def unpack565(c):
    r = (c >> 11) & 0x1F
    g = (c >> 5) & 0x3F
    b = c & 0x1F
    r = (r << 3) | (r >> 2)
    g = (g << 2) | (g >> 4)
    b = (b << 3) | (b >> 2)
    return np.stack([r, g, b], -1).astype(np.int32)


def decode_bc1(data, w, h):
    b = np.frombuffer(data, dtype=np.uint8).reshape(-1, 8)
    c0 = b[:, 0].astype(np.uint16) | (b[:, 1].astype(np.uint16) << 8)
    c1 = b[:, 2].astype(np.uint16) | (b[:, 3].astype(np.uint16) << 8)
    words = (b[:, 4].astype(np.uint32) | (b[:, 5].astype(np.uint32) << 8)
             | (b[:, 6].astype(np.uint32) << 16) | (b[:, 7].astype(np.uint32) << 24))
    p0 = unpack565(c0)
    p1 = unpack565(c1)
    p2 = (2 * p0 + p1) // 3
    p3 = (p0 + 2 * p1) // 3
    pal = np.stack([p0, p1, p2, p3], 1)              # (N,4,3)
    idx = np.zeros((len(b), 16), dtype=np.int32)
    for i in range(16):
        idx[:, i] = (words >> (2 * i)) & 3
    px = pal[np.arange(len(b))[:, None], idx]        # (N,16,3)
    px = px.astype(np.uint8)
    nbx, nby = w // 4, h // 4
    px = px.reshape(nby, nbx, 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(h, w, 3)
    return px


def decode_bc4(data, w, h):
    b = np.frombuffer(data, dtype=np.uint8).reshape(-1, 8)
    a0 = b[:, 0].astype(np.int32)
    a1 = b[:, 1].astype(np.int32)
    pal = np.empty((len(b), 8), np.int32)
    pal[:, 0] = a0
    pal[:, 1] = a1
    for i in range(1, 7):
        pal[:, 1 + i] = ((7 - i) * a0 + i * a1) // 7
    words = np.zeros(len(b), dtype=np.uint64)
    for k in range(6):
        words |= b[:, 2 + k].astype(np.uint64) << np.uint64(8 * k)
    idx = np.zeros((len(b), 16), np.int32)
    for i in range(16):
        idx[:, i] = ((words >> np.uint64(3 * i)) & np.uint64(7)).astype(np.int32)
    px = pal[np.arange(len(b))[:, None], idx].astype(np.uint8)
    nbx, nby = w // 4, h // 4
    return px.reshape(nby, nbx, 4, 4).transpose(0, 2, 1, 3).reshape(h, w)


def psnr(a, b):
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    mse = ((a - b) ** 2).mean()
    if mse == 0:
        return 99.0
    return 10 * np.log10(255.0 ** 2 / mse)


# ---- 1. 合成图（渐变 + 噪声 + alpha），跑 DXT1 / DXT5
rng = np.random.default_rng(1)
n = 256
yy, xx = np.mgrid[0:n, 0:n]
base = np.zeros((n, n, 4), np.uint8)
base[..., 0] = (xx * 255 // n)
base[..., 1] = (yy * 255 // n)
base[..., 2] = 128
base[..., 3] = ((xx + yy) * 255 // (2 * n))
base[..., :3] = np.clip(base[..., :3].astype(np.int16)
                        + rng.integers(-6, 7, (n, n, 3)), 0, 255).astype(np.uint8)

for fmt in ("DXT1", "DXT5"):
    t0 = time.time()
    p = os.path.join(os.path.dirname(OUT), "test_%s.dds" % fmt)
    sz = write_dds(p, base, fmt)
    dt = time.time() - t0
    raw = open(p, "rb").read()
    # 解析第一层
    hdr = raw[:128]
    w_ = int.from_bytes(hdr[16:20], "little")
    h_ = int.from_bytes(hdr[12:16], "little")
    mip = int.from_bytes(hdr[28:32], "little")
    fourcc = hdr[84:88]
    topsz = int.from_bytes(hdr[20:24], "little")
    payload = raw[128:128 + topsz]
    if fmt == "DXT1":
        dec = decode_bc1(payload, w_, h_)
        ref = base[..., :3]
    else:
        col = decode_bc1(payload[::1][0::1][:0], 4, 4) if False else None
        # BC3: 8 字节 alpha + 8 字节 color 交替
        arr = np.frombuffer(payload, np.uint8).reshape(-1, 16)
        ac = decode_bc4(arr[:, :8].tobytes(), w_, h_)
        cc = decode_bc1(arr[:, 8:].tobytes(), w_, h_)
        dec = np.concatenate([cc, ac[..., None]], -1)
        ref = base
    P("%s: %d bytes  头 w=%d h=%d mip=%d fourcc=%s 顶层=%d 耗时 %.2fs"
      % (fmt, sz, w_, h_, mip, fourcc, topsz, dt))
    P("     解码 PSNR(RGB) = %.2f dB   %s" % (psnr(dec[..., :3], ref[..., :3]),
                                              "OK" if psnr(dec[..., :3], ref[..., :3]) > 30 else "偏低"))
    if fmt == "DXT5":
        P("     解码 PSNR(A)   = %.2f dB" % psnr(dec[..., 3], ref[..., 3]))

# ---- 2. 真实贴图：原版 256x256 diffuse 转一次，看体积是否与参考同量级
ref_dds = r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry\PRC_infantry_diffuse.dds"
P("")
P("参考 PRC_infantry_diffuse.dds 大小 = %d bytes" % os.path.getsize(ref_dds))
img = rng.integers(0, 256, (256, 256, 4), np.uint8)
img[..., 3] = 255
p = os.path.join(os.path.dirname(OUT), "test_256.dds")
sz = write_dds(p, img, "DXT1")
P("本编码器 256x256 DXT1 全 mip = %d bytes（参考 43832）" % sz)

# ---- 3. 大图计时
img2 = rng.integers(0, 256, (1024, 1024, 4), np.uint8)
t0 = time.time()
write_dds(os.path.join(os.path.dirname(OUT), "test_1024.dds"), img2, "DXT5")
P("1024x1024 DXT5 全 mip 耗时 %.2fs" % (time.time() - t0))

txt = "\n".join(L)
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)

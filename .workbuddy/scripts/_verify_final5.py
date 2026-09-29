# -*- coding: utf-8 -*-
"""核验 terrain_final5*.bmp 的位深 / 索引结构 / 调色板是否合规。"""
import struct, os, collections, sys, io

SRC = r"C:\Users\XIANGZIYUAN\hoi4lint"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\scripts\_verify_final5.txt"

# 原版 00_terrain.txt 的索引 -> 地形语义（已在前序工作中锁定）
IDX2NAME = {
    0: ("plains", "texture 1"), 1: ("forest", "texture 4"), 2: ("hills", "texture 3"),
    3: ("desert", "texture 9"), 4: ("forest", "texture 4"), 5: ("plains", "texture 1"),
    6: ("mountain", "texture 11"), 7: ("desert", "texture 9"), 8: ("desert", "texture 9"),
    9: ("marsh", "texture 6"), 10: ("mountain", "texture 11"), 11: ("mountain", "texture 11"),
    12: ("desert", "texture 9"), 13: ("urban", "texture 10"), 14: ("lakes", "texture 255"),
    15: ("ocean", "texture 9"), 16: ("mountain", "texture 11"), 17: ("hills", "texture 3"),
    18: ("mountain", "texture 11"), 19: ("plains", "texture 1"), 20: ("mountain", "texture 11"),
    21: ("jungle", "texture 4"), 22: ("jungle", "texture 4"), 27: ("mountain", "texture 11"),
    31: ("mountain", "texture 11"),
}


def parse_header(path):
    with open(path, 'rb') as f:
        b = f.read(64)
    sig = b[0:2]
    fsize = struct.unpack_from('<I', b, 2)[0]
    off = struct.unpack_from('<I', b, 10)[0]
    dib = struct.unpack_from('<I', b, 14)[0]
    w, h = struct.unpack_from('<ii', b, 18)
    planes, bpp = struct.unpack_from('<HH', b, 26)
    comp = struct.unpack_from('<I', b, 30)[0]
    clrused = struct.unpack_from('<I', b, 46)[0]
    real = os.path.getsize(path)
    return dict(sig=sig, fsize=fsize, off=off, dib=dib, w=w, h=h,
                planes=planes, bpp=bpp, comp=comp, clrused=clrused, real=real)


def read_palette(path, hdr):
    n = hdr['clrused'] or (hdr['off'] - 14 - hdr['dib']) // 4
    with open(path, 'rb') as f:
        f.seek(14 + hdr['dib'])
        raw = f.read(n * 4)
    pal = []
    for i in range(n):
        b, g, r, _ = raw[i * 4:i * 4 + 4]
        pal.append((r, g, b))
    return pal


def read_pixels(path, hdr):
    row = (hdr['w'] * hdr['bpp'] + 7) // 8
    pad = (-row) % 4
    stride = row + pad
    with open(path, 'rb') as f:
        f.seek(hdr['off'])
        data = f.read(stride * abs(hdr['h']))
    assert len(data) == stride * abs(hdr['h']), (len(data), stride * abs(hdr['h']))
    rows = []
    for y in range(abs(hdr['h'])):
        rows.append(data[y * stride:y * stride + row])
    return rows, stride, pad


lines = []
P = lambda s='': lines.append(s)

files = [
    ("terrain_final5.bmp", os.path.join(SRC, "terrain_final5.bmp")),
    ("terrain_final5_8bit.bmp", os.path.join(SRC, "terrain_final5_8bit.bmp")),
]
MAPPED = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
files.append(("map/terrain.bmp (当前装机)", os.path.join(MAPPED, "terrain.bmp")))
files.append(("map/terrain_24bit_painting.bmp", os.path.join(MAPPED, "terrain_24bit_painting.bmp")))
files.append(("map/terrain_02.bmp", os.path.join(MAPPED, "terrain_02.bmp")))

for label, path in files:
    P("=" * 78)
    if not os.path.exists(path):
        P(f"{label}  ->  文件不存在: {path}")
        continue
    h = parse_header(path)
    idxed = (h['bpp'] == 8 and h['comp'] == 0 and h['clrused'] != 0
             or (h['bpp'] == 8 and h['comp'] == 0))
    P(f"{label}")
    P(f"  路径        : {path}")
    P(f"  签名        : {h['sig']!r}")
    P(f"  实际字节    : {h['real']:,}")
    P(f"  头声明字节  : {h['fsize']:,}   与实物一致={h['fsize']==h['real']}")
    P(f"  DIB 头长    : {h['dib']}")
    P(f"  尺寸        : {h['w']} x {h['h']}")
    P(f"  位深 bpp    : {h['bpp']}")
    P(f"  压缩方式    : {h['comp']}  (0=BI_RGB 无压缩)")
    P(f"  像素偏移    : {h['off']}   调色板字节 = {h['off']-14-h['dib']}  -> 颜色数 = {(h['off']-14-h['dib'])//4}")
    P(f"  ClrUsed字段 : {h['clrused']}")
    verdict = "8 位索引图(调色板型)" if (h['bpp'] == 8 and h['comp'] == 0) else f"{h['bpp']} 位真彩色(非索引)"
    P(f"  >>> 结论    : {verdict}")

    if h['bpp'] != 8:
        continue

    pal = read_palette(path, h)
    rows, stride, pad = read_pixels(path, h)
    # BMP 行自下而上
    hist = collections.Counter()
    for raw in rows:
        hist.update(raw[:h['w']])
    total = sum(hist.values())
    P(f"  行跨距      : {stride} (有效 {h['w']} + 补位 {pad})")
    P(f"  像素总数    : {total:,}")
    P(f"  调色板项数  : {len(pal)}")
    P(f"  实际用到索引: {len(hist)} 个")
    P("  索引明细:")
    undef = []
    for k in sorted(hist):
        nm = IDX2NAME.get(k)
        if nm:
            P(f"    idx {k:3d}  {hist[k]:>10,} px   {nm[0]:9s} {nm[1]:12s} 调色板色 = {pal[k] if k < len(pal) else 'N/A'}")
        else:
            P(f"    idx {k:3d}  {hist[k]:>10,} px   ** 00_terrain.txt 中未定义 **  调色板色 = {pal[k] if k < len(pal) else 'N/A'}")
            undef.append(k)
    P(f"  未定义索引  : {undef if undef else '无（全部落在已定义编号上）'}")
    P(f"  索引越界    : {'无' if max(hist) < len(pal) else '有！max idx = %d >= 调色板 %d' % (max(hist), len(pal))}")

    # 顶部/底部行抽样，确认行序
    P(f"  第 0 行(文件首行=图像末行) 前 12 像素: {list(rows[0][:12])}")
    P(f"  第 -1 行(文件末行=图像首行) 前 12 像素: {list(rows[-1][:12])}")

P("=" * 78)
P("")
P("对照：原版仓库 terrain.bmp 基线 = 8,389,682 字节 / 偏移 1074 / 255 色板（git HEAD 记录）")
P("")
P("调色板全 256 项（8bit 文件）:")
h = parse_header(os.path.join(SRC, "terrain_final5_8bit.bmp"))
pal = read_palette(os.path.join(SRC, "terrain_final5_8bit.bmp"), h)
rows, stride, pad = read_pixels(os.path.join(SRC, "terrain_final5_8bit.bmp"), h)
hist = collections.Counter()
for raw in rows:
    hist.update(raw[:h['w']])
for k in sorted(hist):
    nm = IDX2NAME.get(k, ("未定义", ""))
    P(f"  idx {k:3d} = {pal[k] if k < len(pal) else 'N/A'}   {nm[0]} {nm[1]}")

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("written:", OUT)

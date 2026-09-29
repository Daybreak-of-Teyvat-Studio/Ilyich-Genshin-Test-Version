# -*- coding: utf-8 -*-
"""把用户画好的 24 位 terrain.bmp 转成 HOI4 需要的 8 位索引 BMP，并校正调色板。"""
import struct, os, collections
import numpy as np
from scipy import ndimage as ndi

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
REP   = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_build.txt"

# 颜色 -> 地形 colormap ID（依据 00_terrain.txt 与本仓库 git 版本确立的配色约定）
BASE = [
    ((0,   0, 255), 15),   # ocean
    ((27, 27,  27), 27),   # mountain
    ((76, 96,  35),  9),   # marsh
    ((124,135,125), 11),   # mountain
    ((255,129, 66),  0),   # plains
    ((89,199,  85),  1),   # forest
    ((128,128,128), 13),   # urban
    ((155,  0,255), 13),   # urban(旧紫) -> 同归 13
    ((127,191,  0), 21),   # jungle
    ((248,255,153), 17),   # hills
    ((255, 63,  0),  3),   # desert
    ((0, 255,255),  14),   # lakes
]
# 输出调色板（每索引的代表色）
PAL = {0:(255,129,66), 1:(89,199,85), 3:(255,63,0), 9:(76,96,35),
       11:(124,135,125), 13:(128,128,128), 14:(0,255,255), 15:(0,0,255),
       17:(248,255,153), 21:(127,191,0), 27:(27,27,27)}

def hdr(p):
    with open(p, "rb") as f: b = f.read(64)
    return (struct.unpack_from("<I", b, 10)[0], struct.unpack_from("<I", b, 14)[0],
            struct.unpack_from("<ii", b, 18)[0], struct.unpack_from("<ii", b, 18)[1],
            struct.unpack_from("<HH", b, 26)[1])

def read8(p):
    off, hs, w, h, bpp = hdr(p)
    with open(p, "rb") as f:
        f.seek(off); d = np.frombuffer(f.read(w*h), dtype=np.uint8).reshape(h, w)
    return d[::-1]

def read24(p):
    off, hs, w, h, bpp = hdr(p)
    rb = ((w*3+3)//4)*4
    with open(p, "rb") as f:
        f.seek(off); raw = f.read(rb*h)
    a = np.frombuffer(raw, dtype=np.uint8).reshape(h, rb)[:, :w*3].reshape(h, w, 3)
    return a[::-1][:, :, ::-1]           # -> RGB, top-down

def write8(path, idx, pal256):
    h, w = idx.shape
    rb = (w + 3) // 4 * 4
    row = np.zeros((h, rb), dtype=np.uint8)
    row[:, :w] = idx
    data = row[::-1].tobytes()            # bottom-up
    off = 54 + 1024
    size = off + len(data)
    fh = b"BM" + struct.pack("<IHHI", size, 0, 0, off)
    ih = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 8, 0, len(data), 0, 0, 256, 0)
    plt = b"".join(bytes((b, g, r, 0)) for (r, g, b) in pal256)
    assert len(plt) == 1024
    with open(path, "wb") as f:
        f.write(fh); f.write(ih); f.write(plt); f.write(data)

L = []
T = read24(os.path.join(GAMMA, "terrain.bmp"))
H = read8(os.path.join(GAMMA, "heightmap.bmp"))
h, w = H.shape
L.append(f"source terrain.bmp {T.shape} / heightmap {H.shape}")

# 1) 建立像素->ID 查表
lut = np.zeros(256*256*256, dtype=np.int32)
kol = ((T[:, :, 0].astype(np.int32) << 16) | (T[:, :, 1].astype(np.int32) << 8) | T[:, :, 2].astype(np.int32))
uniq = np.unique(kol)
L.append(f"unique colors in painting = {len(uniq)}")
lut_maps = {}
for c in uniq:
    c = int(c)
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    exact = [i for ((cr, cg, cb), i) in BASE if (cr, cg, cb) == (r, g, b)]
    if exact:
        lut_maps[c] = exact[0]; tag = "exact"
    else:
        d = [abs(r-cr)+abs(g-cg)+abs(b-cb) for ((cr, cg, cb), _) in BASE]
        j = int(np.argmin(d)); lut_maps[c] = BASE[j][1]
        tag = f"nearest->{BASE[j][1]} (dist {d[j]})"
    n = int((kol == c).sum())
    if n >= 100:
        L.append(f"   ({r:3d},{g:3d},{b:3d}) px={n:8d}  {tag}")

idx = np.vectorize(lut_maps.__getitem__, otypes=[np.int32])(kol)
L.append("")
L.append("=== stage1: from painting ===")
for i, n in sorted(collections.Counter(idx.ravel().tolist()).items()):
    L.append(f"   idx {i:3d}: {n:9d}")

# 2) 海平面校正：高度 < 96 一律为 ocean(15)
sea = H < 96
before = int(((idx != 15) & sea).sum())
idx[sea] = 15
L.append("")
L.append(f"=== stage2: sea-level fix (H<96 -> 15): {before} px changed ===")
rev = int(((idx == 15) & ~sea).sum())
L.append(f"   (reference only) ocean index on land (H>=96): {rev} px, left untouched")

# 3) 统计碎片
L.append("")
L.append("=== stage3: blob stats (连通块) ===")
st = ndi.generate_binary_structure(2, 2)
for i in sorted(set(idx.ravel().tolist())):
    m = idx == i
    lab, n = ndi.label(m, structure=st)
    if n == 0: continue
    sizes = np.bincount(lab.ravel())[1:]
    tiny = int((sizes <= 3).sum())
    L.append(f"   idx {i:3d}: blobs={n:6d}  px={int(m.sum()):8d}  <=3px blobs={tiny:5d}  "
             f"(they cover {int(sizes[sizes<=3].sum()):6d} px)")

# 4) 写盘
pal256 = [(0, 0, 0)] * 256
for k, v in PAL.items():
    pal256[k] = v
out = os.path.join(GAMMA, "terrain_8bit_indexed.bmp")
write8(out, idx.astype(np.uint8), pal256)
L.append("")
L.append(f"=== written: {out} size={os.path.getsize(out)} ===")

# 5) 预览 PNG
from PIL import Image
rgb = np.zeros((h, w, 3), dtype=np.uint8)
for k, v in PAL.items():
    rgb[idx == k] = v
img = Image.fromarray(rgb)
img.save(r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\preview\10_final_indexed.png")
img.resize((w//3, h//3), Image.NEAREST).save(
    r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\preview\10b_final_small.png")

with open(REP, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("ok")

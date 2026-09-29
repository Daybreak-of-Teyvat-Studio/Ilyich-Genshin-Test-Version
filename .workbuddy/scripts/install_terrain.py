# -*- coding: utf-8 -*-
"""安装校正后的 8 位索引 terrain.bmp，并重建被误覆盖的 terrain_01.bmp。"""
import struct, os, collections
import numpy as np

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
REP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_install.txt"

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
    return a[::-1][:, :, ::-1]

def write24(path, rgb):
    h, w = rgb.shape[:2]
    rb = ((w*3+3)//4)*4
    row = np.zeros((h, rb), dtype=np.uint8)
    row[:, :w*3] = rgb[:, :, ::-1].reshape(h, w*3)     # -> BGR
    data = row[::-1].tobytes()
    off = 54
    fh = b"BM" + struct.pack("<IHHI", off + len(data), 0, 0, off)
    ih = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(data), 0, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(fh); f.write(ih); f.write(data)

L = []
# --- 1) 备份用户手绘的 24 位原稿 ---
src = os.path.join(G, "terrain.bmp")
paint = read24(src)
write24(os.path.join(G, "terrain_24bit_painting.bmp"), paint)
L.append(f"backup painted 24bit -> terrain_24bit_painting.bmp  {paint.shape}")

# --- 2) 用校正稿覆盖 terrain.bmp ---
with open(os.path.join(G, "terrain_8bit_indexed.bmp"), "rb") as f:
    newdata = f.read()
with open(src, "wb") as f:
    f.write(newdata)
L.append(f"installed terrain.bmp  bytes={len(newdata)}")

# --- 3) 重建 terrain_01.bmp（24 位、11 色调色板版本） ---
BASE = [((0,0,255),15),((27,27,27),27),((76,96,35),9),((124,135,125),11),
        ((255,129,66),0),((89,199,85),1),((128,128,128),13),((155,0,255),13),
        ((127,191,0),21),((248,255,153),17),((255,63,0),3),((0,255,255),14)]
ORIG = {0:(255,129,66),1:(89,199,85),3:(255,63,0),9:(76,96,35),11:(124,135,125),
        13:(155,0,255),14:(0,255,255),15:(0,0,255),17:(248,255,153),
        21:(127,191,0),27:(27,27,27)}
kol = (paint[:,:,0].astype(np.int32)<<16)|(paint[:,:,1].astype(np.int32)<<8)|paint[:,:,2].astype(np.int32)
m = {}
for c in np.unique(kol):
    c = int(c); r,g,b = (c>>16)&255,(c>>8)&255,c&255
    ex = [i for (cc,i) in BASE if cc==(r,g,b)]
    if ex: m[c]=ex[0]
    else:
        d=[abs(r-a)+abs(g-b2)+abs(b-cc2) for ((a,b2,cc2),_) in BASE]
        m[c]=BASE[int(np.argmin(d))][1]
idx0 = np.vectorize(m.__getitem__, otypes=[np.int32])(kol)
rgb = np.zeros(idx0.shape+(3,), dtype=np.uint8)
for k,v in ORIG.items():
    rgb[idx0==k] = v
write24(os.path.join(G, "terrain_01.bmp"), rgb)
L.append("rebuilt terrain_01.bmp (24bit / 11-colour intermediate)")

# --- 4) 校验 ---
off, hs, w, h, bpp = hdr(src)
L.append("")
L.append(f"VERIFY terrain.bmp: off={off} hs={hs} {w}x{h} bpp={bpp} clrused="
         f"{struct.unpack_from('<I', open(src,'rb').read(64), 46)[0]} size={os.path.getsize(src)}")
d = read8(src)
c = collections.Counter(d.ravel().tolist())
L.append("index histogram:")
for i, n in sorted(c.items()):
    L.append(f"   idx {i:3d}: {n:9d}")
inv = [i for i in c if not (i <= 22 or i in (27, 31))]
L.append(f"INVALID terrain indices present: {inv}")

with open(REP, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("ok")

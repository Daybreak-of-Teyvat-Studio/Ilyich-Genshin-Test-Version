# -*- coding: utf-8 -*-
import struct, os
import numpy as np

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
OUT   = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\scripts\_matrix.txt"

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
    return a[::-1][:, :, ::-1]      # -> RGB

T2 = read8(os.path.join(GAMMA, "terrain_02.bmp"))
T  = read24(os.path.join(GAMMA, "terrain.bmp"))
M  = read8(os.path.join(GAMMA, "terrain_merged_8bit.bmp"))

# index plane of user's painting: nearest of merged palette
mp = {}
def read_pal(p):
    off, hs, w, h, bpp = hdr(p); ps = 14+hs
    with open(p, "rb") as f:
        f.seek(ps); raw = f.read((off-ps)//4*4)
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, 4)[:, [2, 1, 0]]
palm = read_pal(os.path.join(GAMMA, "terrain_merged_8bit.bmp"))

used = [0, 1, 3, 9, 11, 13, 14, 15, 17, 21, 27]
key = (T[:, :, 0].astype(np.int32) << 16) | (T[:, :, 1].astype(np.int32) << 8) | T[:, :, 2].astype(np.int32)

L = []
L.append("=== user base colors vs merged palette ===")
for i in used:
    c = tuple(int(x) for x in palm[i])
    n = int((key == (c[0] << 16 | c[1] << 8 | c[2])).sum())
    L.append(f"  merged idx {i:2d} RGB={c}  px_in_user_file(24bit)={n}  px_in_merged={int((M==i).sum())}")

t2vals = sorted(set(T2.ravel().tolist()))
usercols = {}
for i in used:
    c = tuple(int(x) for x in palm[i])
    usercols[i] = c

L.append("")
L.append("=== overlap matrix: rows = terrain_02 idx (px), cols = user color (merged idx) ===")
hdrline = "  t02\\usr " + " ".join(f"{i:>9d}" for i in used)
L.append(hdrline)
for v in t2vals:
    m2 = T2 == v
    n2 = int(m2.sum())
    row = []
    for i in used:
        c = usercols[i]
        kk = (c[0] << 16) | (c[1] << 8) | c[2]
        row.append(int(((key == kk) & m2).sum()))
    L.append(f"  {v:7d} " + " ".join(f"{x:9d}" for x in row) + f"   total={n2}")

# also: merged idx vs terrain_02 idx overlap
L.append("")
L.append("=== overlap: terrain_02 idx vs merged idx (px) ===")
L.append("  t02\\mrg " + " ".join(f"{i:>9d}" for i in used))
for v in t2vals:
    m2 = T2 == v
    row = [int(((M == i) & m2).sum()) for i in used]
    L.append(f"  {v:7d} " + " ".join(f"{x:9d}" for x in row))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("ok")

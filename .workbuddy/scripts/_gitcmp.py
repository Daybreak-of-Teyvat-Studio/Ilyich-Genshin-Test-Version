# -*- coding: utf-8 -*-
import struct, os, collections
import numpy as np

D = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\gitref"
G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
OUT = os.path.join(D, "_gitcmp.txt")

def load(p):
    with open(p, "rb") as f:
        b = f.read(64)
    off = struct.unpack_from("<I", b, 10)[0]
    hs = struct.unpack_from("<I", b, 14)[0]
    w, h = struct.unpack_from("<ii", b, 18)
    bpp = struct.unpack_from("<HH", b, 26)[1]
    ps = 14 + hs
    with open(p, "rb") as f:
        f.seek(ps); pal = f.read(max(0, off - ps))
        f.seek(off); data = f.read(w*h)
    pal = np.frombuffer(pal, dtype=np.uint8).reshape(-1, 4)[:, [2, 1, 0]] if pal else None
    return off, hs, w, h, bpp, pal, np.frombuffer(data, dtype=np.uint8)

L = []
for tag, p in [("head_terrain", os.path.join(D, "head_terrain.bmp")),
               ("c1c81_terrain", os.path.join(D, "c1c81_terrain.bmp")),
               ("cf918_terrain", os.path.join(D, "cf918_terrain.bmp")),
               ("map/terrain_02", os.path.join(G, "terrain_02.bmp"))]:
    if not os.path.exists(p):
        L.append(f"[MISSING] {tag}"); continue
    off, hs, w, h, bpp, pal, d = load(p)
    c = collections.Counter(d.tolist())
    L.append(f"--- {tag}: off={off} hs={hs} {w}x{h} bpp={bpp} palEntries={0 if pal is None else len(pal)} used={len(c)}")
    for i in sorted(c):
        rgb = tuple(int(x) for x in pal[i]) if pal is not None and i < len(pal) else None
        L.append(f"     idx {i:3d}: px={c[i]:9d} palRGB={rgb}")
    hi = sum(v for k, v in c.items() if k > 22 and k not in (27, 31))
    L.append(f"     [invalid-in-vanilla-idx px] = {hi}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("ok")

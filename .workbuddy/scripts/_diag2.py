# -*- coding: utf-8 -*-
import struct, os, collections, json
import numpy as np

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
VAN   = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\map"
OUT   = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\scripts\_diag2.txt"

def hdr(p):
    with open(p, "rb") as f:
        b = f.read(64)
    (off,) = struct.unpack_from("<I", b, 10)
    (hs,) = struct.unpack_from("<I", b, 14)
    w, h = struct.unpack_from("<ii", b, 18)
    bpp = struct.unpack_from("<H", b, 26)[0]
    clrused = struct.unpack_from("<I", b, 46)[0]
    return off, hs, w, h, bpp, clrused

def load_pal(p):
    off, hs, w, h, bpp, clrused = hdr(p)
    palstart = 14 + hs
    n = (off - palstart) // 4
    if n <= 0:
        return None, 0
    with open(p, "rb") as f:
        f.seek(palstart)
        raw = f.read(n * 4)
    pal = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 4)
    return pal, n

L = []
for tag, p in [("VANILLA terrain.bmp", os.path.join(VAN, "terrain.bmp")),
               ("VANILLA heightmap.bmp", os.path.join(VAN, "heightmap.bmp")),
               ("gamma terrain_02.bmp", os.path.join(GAMMA, "terrain_02.bmp")),
               ("gamma terrain_merged_8bit.bmp", os.path.join(GAMMA, "terrain_merged_8bit.bmp")),
               ("gamma heightmap.bmp", os.path.join(GAMMA, "heightmap.bmp")),
               ("gamma cities.bmp", os.path.join(GAMMA, "cities.bmp"))]:
    if not os.path.exists(p):
        L.append(f"[MISSING] {tag}")
        continue
    off, hs, w, h, bpp, clrused = hdr(p)
    L.append(f"{tag}: off={off} hs={hs} {w}x{h} bpp={bpp} clrused={clrused} size={os.path.getsize(p)}")

L.append("")
L.append("=== VANILLA terrain.bmp palette (BGRA) ===")
pal, n = load_pal(os.path.join(VAN, "terrain.bmp"))
L.append(f"palette entries = {n}")
for i in range(n):
    b_, g_, r_, a_ = int(pal[i][0]), int(pal[i][1]), int(pal[i][2]), int(pal[i][3])
    L.append(f"  idx {i:3d}: BGR=({b_:3d},{g_:3d},{r_:3d}) A={a_}")

# vanilla index histogram
off, hs, w, h, bpp, clrused = hdr(os.path.join(VAN, "terrain.bmp"))
with open(os.path.join(VAN, "terrain.bmp"), "rb") as f:
    f.seek(off)
    d = np.frombuffer(f.read(w * h), dtype=np.uint8)
c = collections.Counter(d.tolist())
L.append("")
L.append(f"=== VANILLA terrain.bmp index histogram ({len(c)} used) ===")
for i in sorted(c):
    r_, g_, b_ = int(pal[i][2]), int(pal[i][1]), int(pal[i][0])
    L.append(f"  idx {i:3d}: px={c[i]:9d}  RGB=({r_:3d},{g_:3d},{b_:3d})")

# terrain_02 correct palette
L.append("")
for tag, fn in [("gamma terrain_02.bmp", "terrain_02.bmp"),
                ("gamma terrain_merged_8bit.bmp", "terrain_merged_8bit.bmp")]:
    p = os.path.join(GAMMA, fn)
    pal2, n2 = load_pal(p)
    off, hs, w, h, bpp, clrused = hdr(p)
    with open(p, "rb") as f:
        f.seek(off)
        d = np.frombuffer(f.read(w * h), dtype=np.uint8)
    c = collections.Counter(d.tolist())
    L.append(f"=== {tag} palette n={n2} ===")
    for i in sorted(c):
        r_, g_, b_ = int(pal2[i][2]), int(pal2[i][1]), int(pal2[i][0])
        L.append(f"  idx {i:3d}: px={c[i]:9d}  RGB=({r_:3d},{g_:3d},{b_:3d})")

# 24-bit RGB histogram of user-painted terrain.bmp
L.append("")
for fn in ["terrain.bmp", "terrain_01.bmp"]:
    p = os.path.join(GAMMA, fn)
    if not os.path.exists(p):
        continue
    off, hs, w, h, bpp, clrused = hdr(p)
    if bpp != 24:
        L.append(f"{fn}: not 24-bit, skipped")
        continue
    rowbytes = ((w * 3 + 3) // 4) * 4
    with open(p, "rb") as f:
        f.seek(off)
        raw = f.read(rowbytes * h)
    a = np.frombuffer(raw, dtype=np.uint8).reshape(h, rowbytes)[:, :w*3].reshape(h, w, 3)
    a = a[::-1]  # flip to top-down
    rgb = a[:, :, ::-1].reshape(-1, 3)
    uniq, cnt = np.unique(rgb, axis=0, return_counts=True)
    order = np.argsort(-cnt)
    L.append(f"=== {fn} 24-bit  unique colors={len(uniq)} ===")
    for k in order[:40]:
        r_, g_, b_ = int(uniq[k][0]), int(uniq[k][1]), int(uniq[k][2])
        L.append(f"  RGB=({r_:3d},{g_:3d},{b_:3d}) px={int(cnt[k]):9d}")
    if len(uniq) > 40:
        L.append(f"  ... {len(uniq)-40} more colors, total tail px={int(cnt[order[40:]].sum())}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("ok")

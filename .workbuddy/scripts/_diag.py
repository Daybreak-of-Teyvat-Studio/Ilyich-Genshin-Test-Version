# -*- coding: utf-8 -*-
"""Dump BMP headers + palettes for all terrain candidates."""
import struct, os, collections
import numpy as np

MAP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\scripts\_diag.txt"

FILES = [
    "terrain.bmp", "terrain_01.bmp", "terrain_02.bmp",
    "terrain_merged.bmp", "terrain_merged_8bit.bmp",
    "heightmap.bmp", "heightmap_01.bmp",
    "provinces.bmp", "cities.bmp", "world_normal.bmp", "trees.bmp",
]

lines = []

def hdr(p):
    with open(p, "rb") as f:
        b = f.read(64)
    sig = b[:2]
    (fsize,) = struct.unpack_from("<I", b, 2)
    (off,) = struct.unpack_from("<I", b, 10)
    (hs,) = struct.unpack_from("<I", b, 14)
    w, h = struct.unpack_from("<ii", b, 18)
    planes, bpp = struct.unpack_from("<HH", b, 26)
    comp, imgsz = struct.unpack_from("<II", b, 30)
    clrused = struct.unpack_from("<I", b, 46)[0]
    return dict(sig=sig, fsize=fsize, off=off, hs=hs, w=w, h=h, planes=planes,
                bpp=bpp, comp=comp, imgsz=imgsz, clrused=clrused,
                real=os.path.getsize(p))

for name in FILES:
    p = os.path.join(MAP, name)
    if not os.path.exists(p):
        lines.append(f"[MISSING] {name}")
        continue
    d = hdr(p)
    exp = d["off"] + abs(d["w"]) * abs(d["h"]) * (d["bpp"] // 8)
    lines.append(
        f"{name:28s} sig={d['sig']} bpp={d['bpp']:2d} {d['w']}x{d['h']} "
        f"comp={d['comp']} off={d['off']} clrused={d['clrused']} "
        f"real={d['real']} exp={exp} delta={d['real']-exp}")

lines.append("")
lines.append("=== palettes of 8-bit candidates ===")
for name in FILES:
    p = os.path.join(MAP, name)
    if not os.path.exists(p):
        continue
    d = hdr(p)
    if d["bpp"] != 8:
        continue
    n = d["clrused"] or 256
    n = min(n, 256, (d["off"] - d["hs"]) // 4)
    with open(p, "rb") as f:
        f.seek(d["hs"])
        pal = f.read(n * 4)
    used = collections.Counter()
    with open(p, "rb") as f:
        f.seek(d["off"])
        data = f.read(abs(d["w"]) * abs(d["h"]))
    used = collections.Counter(data)
    lines.append(f"--- {name}  used_index_count={len(used)}")
    for i in sorted(used):
        r, g, b = pal[i*4], pal[i*4+1], pal[i*4+2]
        lines.append(f"   idx {i:3d} (0x{i:02X}) rgb=({r:3d},{g:3d},{b:3d}) px={used[i]}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done")

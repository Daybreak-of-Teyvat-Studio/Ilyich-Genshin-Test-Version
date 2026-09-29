# -*- coding: utf-8 -*-
import struct, os, collections
import numpy as np
from PIL import Image

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
WORK  = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\preview"
os.makedirs(WORK, exist_ok=True)

def hdr(p):
    with open(p, "rb") as f:
        b = f.read(64)
    off = struct.unpack_from("<I", b, 10)[0]
    hs  = struct.unpack_from("<I", b, 14)[0]
    w, h = struct.unpack_from("<ii", b, 18)
    planes, bpp = struct.unpack_from("<HH", b, 26)
    return off, hs, w, h, bpp

def read8(p):
    off, hs, w, h, bpp = hdr(p)
    with open(p, "rb") as f:
        f.seek(off)
        d = np.frombuffer(f.read(w*h), dtype=np.uint8).reshape(h, w)
    return d[::-1]

def read24(p):
    off, hs, w, h, bpp = hdr(p)
    rb = ((w*3+3)//4)*4
    with open(p, "rb") as f:
        f.seek(off)
        raw = f.read(rb*h)
    a = np.frombuffer(raw, dtype=np.uint8).reshape(h, rb)[:, :w*3].reshape(h, w, 3)
    return a[::-1]

def read_pal(p):
    off, hs, w, h, bpp = hdr(p)
    ps = 14 + hs
    n = (off - ps) // 4
    with open(p, "rb") as f:
        f.seek(ps)
        raw = f.read(n*4)
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, 4)[:, [2, 1, 0]]

def save(arr, name, scale=3):
    h, w = arr.shape[:2]
    img = Image.fromarray(arr.astype(np.uint8))
    img = img.resize((w//scale, h//scale), Image.NEAREST)
    img.save(os.path.join(WORK, name))

T = read24(os.path.join(GAMMA, "terrain.bmp"))
save(T[:, :, ::-1], "01_terrain_raw_asStored.png")
save(T, "02_terrain_unswapped.png")

T2 = read8(os.path.join(GAMMA, "terrain_02.bmp"))
pal2 = read_pal(os.path.join(GAMMA, "terrain_02.bmp"))
save(pal2[T2.astype(np.int64)], "03_terrain02_ownpalette.png")

m = read8(os.path.join(GAMMA, "terrain_merged_8bit.bmp"))
palm = read_pal(os.path.join(GAMMA, "terrain_merged_8bit.bmp"))
save(palm[m.astype(np.int64)], "04_merged_ownpalette.png")

Hh = read8(os.path.join(GAMMA, "heightmap.bmp"))
save(np.stack([Hh]*3, axis=-1), "05_heightmap.png")

L = []
L.append(f"terrain02 palette non-black entries: {[i for i in range(len(pal2)) if tuple(pal2[i])!=(0,0,0)]}")
L.append(f"merged  palette non-black entries: {[i for i in range(len(palm)) if tuple(palm[i])!=(0,0,0)]}")
with open(os.path.join(WORK, "_p.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("ok")

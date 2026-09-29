# -*- coding: utf-8 -*-
import struct, os
import numpy as np
from PIL import Image

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
P = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\preview"

PAL = {0:(255,129,66), 1:(89,199,85), 3:(255,63,0), 9:(76,96,35),
       11:(124,135,125), 13:(128,128,128), 14:(0,255,255), 15:(0,0,255),
       17:(248,255,153), 21:(127,191,0), 27:(27,27,27)}

def read8(p):
    with open(p, "rb") as f: b = f.read(64)
    off = struct.unpack_from("<I", b, 10)[0]
    w, h = struct.unpack_from("<ii", b, 18)
    with open(p, "rb") as f:
        f.seek(off); d = np.frombuffer(f.read(w*h), dtype=np.uint8).reshape(h, w)
    return d[::-1]

idx = read8(os.path.join(G, "terrain_8bit_indexed.bmp"))
rgb = np.zeros(idx.shape + (3,), dtype=np.uint8)
for k, v in PAL.items():
    rgb[idx == k] = v

# 陆地主要区域裁切
x0, y0, s = 1700, 800, 900
crop = rgb[y0:y0+s, x0:x0+s]
Image.fromarray(crop).save(os.path.join(P, "11_crop_main.png"))

x0, y0, s = 2100, 350, 600
crop2 = rgb[y0:y0+s, x0:x0+s]
Image.fromarray(crop2).resize((s*2, s*2), Image.NEAREST).save(os.path.join(P, "12_crop_zoom2x.png"))
print("ok")

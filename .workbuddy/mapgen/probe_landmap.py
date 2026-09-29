# -*- coding: utf-8 -*-
import os, io, struct
import numpy as np
from PIL import Image

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
D = os.path.join(GAMMA, ".workbuddy", "heightmap_soft")

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

for name in ["DOT MAP 3.0.bmp", "DOT MAP 3.0 C.bmp", "DOT MAP 3.0 P.bmp", "DOT MAP 2.0.bmp",
             "DOT MAP 3.0.png", "7.2-1.bmp"]:
    p = os.path.join(GAMMA, ".workbuddy", name)
    if not os.path.isfile(p):
        P("%-22s 不存在" % name); continue
    raw = open(p, "rb").read(60)
    off = struct.unpack("<I", raw[10:14])[0]
    hs, w, h, pl, bpp, comp, isz = struct.unpack("<IiiHHII", raw[14:38])
    im = Image.open(p)
    P("%-22s size=%s mode=%s bpp=%d off=%d bytes=%d" % (name, im.size, im.mode, bpp, off, os.path.getsize(p)))

P("")
P("=" * 70)
p = os.path.join(GAMMA, ".workbuddy", "DOT MAP 3.0.bmp")
im = Image.open(p)
a = np.array(im)
P("DOT MAP 3.0: mode=%s shape=%s dtype=%s" % (im.mode, a.shape, a.dtype))
if a.ndim == 3:
    flat = a.reshape(-1, a.shape[2])
    cols, cnt = np.unique(flat, axis=0, return_counts=True)
    order = np.argsort(cnt)[::-1]
    P("唯一颜色数=%d，前 12 名：" % len(cols))
    for i in order[:12]:
        P("   RGB(%3d,%3d,%3d) = #%02X%02X%02X  %d px (%.3f%%)"
          % (cols[i][0], cols[i][1], cols[i][2], cols[i][0], cols[i][1], cols[i][2],
             cnt[i], 100.0*cnt[i]/len(flat)))
elif a.ndim == 2:
    h2 = np.bincount(a.ravel(), minlength=256)
    order = np.argsort(h2)[::-1]
    P("单通道，前 10 名：")
    for v in order[:10]:
        if h2[v] == 0: break
        P("   %3d : %d (%.3f%%)" % (v, h2[v], 100.0*h2[v]/a.size))

with io.open(os.path.join(D, "landmap_probe.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep))
print("OK")

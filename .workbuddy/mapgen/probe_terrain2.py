# -*- coding: utf-8 -*-
"""搜索 terrain 定义文件 + 分析 heightmap 高值区的分布"""
import os, io, glob
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
VAN = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
H = os.path.join(G, ".workbuddy")
rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

P("===== 搜索 terrain.txt / terrain 定义 =====")
for root in [G, VAN]:
    for dp, dn, fn in os.walk(root):
        if ".workbuddy" in dp or "\\mod\\" in dp:
            continue
        for f in fn:
            if f.lower() == "terrain.txt":
                p = os.path.join(dp, f)
                P("  FOUND", p, os.path.getsize(p))
P("")
for cand in [os.path.join(G, "map", "terrain.txt"),
             os.path.join(VAN, "map", "terrain.txt"),
             os.path.join(G, "common", "terrain", "terrain.txt")]:
    P("  检查:", cand, os.path.isfile(cand))
    if os.path.isfile(cand):
        P(io.open(cand, "r", encoding="utf-8-sig", errors="replace").read())
        P("  ----")
    if cand.endswith(os.path.join(VAN, "map", "terrain.txt")) and os.path.isfile(cand):
        break

P("")
P("===== heightmap 高值区分析 =====")
hm = np.array(Image.open(os.path.join(G, "map", "heightmap.bmp")))
P("  size", hm.shape, "min", hm.min(), "max", hm.max())
land = hm >= 94
P("  陆地像素(>=94):", int(land.sum()))
for lo in range(100, 200, 10):
    n = int(((hm >= lo) & land).sum())
    P("    >=%3d : %6d" % (lo, n))
P("")
P("  细看 150-200 每档:")
hist = np.bincount(hm.ravel(), minlength=256)
for v in range(150, 201):
    if hist[v]:
        P("    %3d : %5d" % (v, int(hist[v])))

P("")
P("  连通块统计（不同阈值）:")
for th in [130, 140, 150, 155, 160, 165, 170, 175, 180]:
    m = (hm >= th) & land
    lab, n = ndi.label(m, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())[1:] if n else np.array([])
    big = sizes[sizes >= 50]
    P("    阈值%-4d 像素%7d  块数%5d   >=50px块数%4d   最大块%6d  面积占比%.2f%%"
      % (th, int(m.sum()), n, len(big), int(sizes.max()) if n else 0,
         100.0 * m.sum() / land.sum()))

io.open(os.path.join(H, "terrain_probe2.txt"), "w", encoding="utf-8").write("\n".join(rep))
print("WROTE")

# -*- coding: utf-8 -*-
"""搜索 terrain 定义 + 地形颜色与 heightmap 高度的交叉统计"""
import os, io
import numpy as np
from PIL import Image

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
VAN = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
H = os.path.join(G, ".workbuddy")
rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

P("===== 搜 terrain 定义（common/terrain 等）=====")
for root in [G, VAN]:
    for sub in ["common\\terrain", "map", "common"]:
        d = os.path.join(root, sub)
        if os.path.isdir(d):
            fs = sorted(os.listdir(d))
            hit = [f for f in fs if "terrain" in f.lower() or f.lower().startswith("00_")]
            if hit:
                P("  %s -> %s" % (d, hit[:12]))
P("")
for cand in [os.path.join(G, "common", "terrain", "00_terrain.txt"),
             os.path.join(VAN, "common", "terrain", "00_terrain.txt")]:
    if os.path.isfile(cand):
        P("===== %s =====" % cand)
        P(io.open(cand, "r", encoding="utf-8-sig", errors="replace").read())
        P("")
        break

P("===== 地形颜色 × 高度 交叉统计 =====")
hm = np.array(Image.open(os.path.join(G, "map", "heightmap.bmp")))
tb = np.array(Image.open(os.path.join(G, "map", "terrain.bmp")))
P("  heightmap", hm.shape, "terrain", tb.shape)
flat = tb.reshape(-1, 3).astype(np.int32)
key = flat[:, 0] * 65536 + flat[:, 1] * 256 + flat[:, 2]
uk, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
hflat = hm.ravel().astype(np.int32)
order = np.argsort(-cnt)
P("")
for i in order:
    r, g, b = uk[i] // 65536, (uk[i] // 256) % 256, uk[i] % 256
    sel = (inv == i)
    vals = hflat[sel]
    if len(vals) > 200000:
        sample = vals[:: max(1, len(vals) // 200000)]
    else:
        sample = vals
    qs = np.percentile(sample, [0, 1, 5, 25, 50, 75, 95, 99, 100])
    P("  #%02X%02X%02X rgb(%3d,%3d,%3d) %8d px | h: min%3d p1 %3d p5 %3d p25 %3d p50 %3d p75 %3d p95 %3d p99 %3d max%3d"
      % (r, g, b, r, g, b, int(cnt[i]), qs[0], qs[1], qs[2], qs[3], qs[4], qs[5], qs[6], qs[7], qs[8]))

# 反过来：每个高度带里各颜色的占比
P("")
P("===== 高度带 × 地形颜色 占比 =====")
land = hm >= 94
COLN = {}
for i in order:
    r, g, b = int(uk[i] // 65536), int((uk[i] // 256) % 256), int(uk[i] % 256)
    COLN[(r, g, b)] = i
bands = [(94, 110), (110, 130), (130, 145), (145, 155), (155, 165), (165, 175), (175, 200)]
head = "  %-12s" % "高度带"
for (r, g, b), i in sorted(COLN.items(), key=lambda kv: -cnt[kv[1]]):
    head += " %8s" % ("%d,%d,%d" % (r, g, b))
P(head)
for lo, hi in bands:
    m = land & (hm >= lo) & (hm < hi)
    tot = int(m.sum())
    row = "  %3d-%-8d" % (lo, hi - 1)
    for (r, g, b), i in sorted(COLN.items(), key=lambda kv: -cnt[kv[1]]):
        sel = m.ravel() & (inv == i)
        row += " %7.2f%%" % (100.0 * sel.sum() / tot) if tot else "       -"
    P(row + "   共%d px" % tot)

io.open(os.path.join(H, "terrain_probe3.txt"), "w", encoding="utf-8").write("\n".join(rep))
print("WROTE")

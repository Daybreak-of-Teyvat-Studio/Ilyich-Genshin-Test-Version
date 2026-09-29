# -*- coding: utf-8 -*-
"""三角形级遮挡测量：眼球表面被脸皮盖住多少（决定需要多大前推量）。

对每个眼球三角的质心 (x,y)，找出所有其在屏幕投影内包含该点的脸皮三角，
插值出脸皮表面的 z；取最靠前（z 最小）者。需要的量 = z_skin - z_eye。
只读。"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_preview as RP  # noqa: E402

MESH = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out3\Vysna_infantry.mesh")

SEG = [("颜", 1942), ("颜2", 1032), ("睫", 1116), ("眉", 52), ("白目", 148),
       ("目", 192), ("瞳", 192), ("目光", 200), ("鼻线", 35), ("口舌", 524),
       ("齿", 144), ("星目", 28)]
acc = 0
b = {}
for nm, c in SEG:
    b[nm] = (acc, acc + c)
    acc += c

nodes = RP.gather(MESH)
face = nodes[1]
P, T = face["P"], face["T"]


def tri_range(names):
    idx = np.concatenate([np.arange(*b[n]) for n in names])
    return P[T[idx]]


skin = tri_range(["颜", "颜2", "睫"])          # 睫也算遮挡物（睫毛在眼球前）
eyes = tri_range(["白目", "目", "瞳", "目光"])
print("脸皮三角 %d  眼球三角 %d" % (len(skin), len(eyes)))

# 眼球质心
ec = eyes.mean(1)

gaps = []
for e in ec:
    x, y = e[0], e[1]
    s = skin
    # 2D 点-三角形测试
    ax, ay, az = s[:, 0, 0], s[:, 0, 1], s[:, 0, 2]
    bx, by, bz = s[:, 1, 0], s[:, 1, 1], s[:, 1, 2]
    cx, cy, cz = s[:, 2, 0], s[:, 2, 1], s[:, 2, 2]
    d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    ok = np.abs(d) > 1e-12
    w0 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy))
    w1 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy))
    w0 = np.where(ok, w0 / np.where(ok, d, 1), -1)
    w1 = np.where(ok, w1 / np.where(ok, d, 1), -1)
    w2 = 1 - w0 - w1
    ins = ok & (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    if not ins.any():
        continue
    zs = w0[ins] * az[ins] + w1[ins] * bz[ins] + w2[ins] * cz[ins]
    gaps.append(zs.min() - e[2])

g = np.array(gaps)
out = []
out.append("眼球三角质心处，脸皮(颜/颜2/睫)表面相对眼球的深度差")
out.append("正值 = 脸皮在眼球前面多少（眼球需要前推超过这个量才可见）")
out.append("=" * 76)
out.append("参与统计的眼球三角: %d / %d（其余质心处没有脸皮覆盖）" % (len(g), len(eyes)))
if len(g):
    out.append("  min   = %8.5f" % g.min())
    out.append("  P50   = %8.5f" % np.percentile(g, 50))
    out.append("  P95   = %8.5f" % np.percentile(g, 95))
    out.append("  P99   = %8.5f" % np.percentile(g, 99))
    out.append("  max   = %8.5f" % g.max())
    out.append("")
    out.append("  -> 建议前推量取 P99/max 之间；若要全部露出，用 max")
    out.append("     当前 EYE_FORWARD 瞳=0.0080, 其余=0.0045")
    out.append("     仅 %d/%d (%.1f%%) 的眼球三角位于脸皮之前"
               % ((g < 0).sum(), len(g), (g < 0).mean() * 100))

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_eye_occlusion.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_eye_occlusion_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % p)

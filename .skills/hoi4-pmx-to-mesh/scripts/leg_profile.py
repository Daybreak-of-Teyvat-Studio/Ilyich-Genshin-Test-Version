# -*- coding: utf-8 -*-
"""按高度分带统计左腿几何的 x 剖面 —— 看大腿/小腿在哪里断掉。

用法: python leg_profile.py <mesh1> [mesh2 ...]
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_render as PR  # noqa: E402

LEG = ("LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase")
HERE = os.path.dirname(os.path.abspath(__file__))
out = []
W = out.append

for mp in sys.argv[1:]:
    bones, geoms = PR.load_mesh(mp)
    names = [b[0] for b in bones]
    idx = {n: i for i, n in enumerate(names)}
    pts, dom = [], []
    for g in geoms:
        if "ix" not in g:
            continue
        arg = np.argmax(g["w"], axis=1)
        d = g["ix"][np.arange(len(g["ix"])), arg]
        keep = g["w"].max(1) > 1e-6
        pts.append(g["P"][keep])
        dom.append(d[keep])
    P = np.concatenate(pts)
    D = np.concatenate(dom)
    isleg = np.zeros(len(P), bool)
    for ln in LEG:
        isleg |= (D == idx[ln])
    P, D = P[isleg], D[isleg]
    P = P[P[:, 0] > 0]          # 只留左腿（x>0）
    D = D[P[:, 0] > 0] if False else D[:len(P)]

    W("=" * 84)
    W("## %s   左腿顶点 %d" % (os.path.basename(os.path.dirname(mp)) + "/"
                              + os.path.basename(mp), len(P)))
    W("=" * 84)
    y0, y1, step = 0.0, 4.0, 0.15
    edges = np.arange(y0, y1 + step, step)
    W("  %-16s %6s  %8s %8s   %s" % ("y 区间(高->低)", "n", "mean x", "mean z", "主导骨构成"))
    for k in range(len(edges) - 2, -1, -1):        # 从高往低打
        lo, hi = edges[k], edges[k + 1]
        sel = (P[:, 1] >= lo) & (P[:, 1] < hi)
        if sel.sum() < 5:
            continue
        comp = {}
        for bn in LEG:
            c = int((D[sel] == idx[bn]).sum())
            if c:
                comp[bn] = c
        W("  %.2f ~ %.2f    %6d  %+8.3f %+8.3f   %s"
          % (hi, lo, int(sel.sum()), P[sel, 0].mean(), P[sel, 2].mean(),
             " ".join("%s=%d" % kv for kv in sorted(comp.items()))))
    # 断点检测：相邻带 mean x 的最大跳变
    xs, ys = [], []
    for k in range(len(edges) - 1):
        sel = (P[:, 1] >= edges[k]) & (P[:, 1] < edges[k + 1])
        if sel.sum() >= 5:
            xs.append(P[sel, 0].mean())
            ys.append(0.5 * (edges[k] + edges[k + 1]))
    if len(xs) > 2:
        d = np.diff(xs) / np.diff(ys)
        j = int(np.argmax(np.abs(d)))
        W("")
        W("  最大 x 梯度：y≈%.2f 处 dx/dy=%+.2f（相邻带跳变 %+.3f）"
          % (ys[j], d[j], np.diff(xs)[j]))
    W("")

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_leg_profile.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_leg_profile_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt)
print("->", p)

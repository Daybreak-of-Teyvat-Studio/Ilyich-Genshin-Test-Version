# -*- coding: utf-8 -*-
"""摆姿势后，各 HOI4 骨骼所驱动的顶点云跑到哪里去了。
重点：mid_back_node（= 翅膀）在 walk 动画下的包围盒。
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_render as PR  # noqa: E402

MESH = sys.argv[1] if len(sys.argv) > 1 else r"../vysna_fix2/Vysna_infantry.mesh"
ANIM = (r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
        r"\gfx\models\units\GER_infantry_moving_rifle.anim")
FRAMES = [int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["0"])]

bones, geoms = PR.load_mesh(MESH)
names = [b[0] for b in bones]

# 记录初始（bind）位置 + 每顶点主骨
init = []
for g in geoms:
    if "ix" not in g:
        init.append(None)
        continue
    arg = np.argmax(g["w"], axis=1)
    dom = g["ix"][np.arange(len(g["ix"])), arg]
    dom = np.where(g["w"].max(1) > 1e-6, dom, -1)
    init.append((g["P"].copy(), dom))

print("%-16s %-28s %s" % ("骨", "bind 包围盒中心/尺寸", "各帧中心/尺寸"))
for target in ("mid_back_node", "Hip", "back_mid", "head"):
    if target not in names:
        continue
    gi = names.index(target)
    rows = []
    for k, g in enumerate(geoms):
        if init[k] is None:
            continue
        P0, dom = init[k]
        sel = dom == gi
        if sel.sum() < 10:
            continue
        rows.append((k, sel, P0[sel]))
    if not rows:
        print("%-16s (无顶点)" % target)
        continue
    for k, sel, p0 in rows:
        c0, s0 = p0.mean(0), p0.max(0) - p0.min(0)
        line = "%-16s n=%6d  c=(%6.2f,%6.2f,%6.2f) size=(%5.2f,%5.2f,%5.2f)" % (
            target, int(sel.sum()), c0[0], c0[1], c0[2], s0[0], s0[1], s0[2])
        for f in FRAMES:
            for g in geoms:
                g["P"] = g["P"].copy()
            # 重新从 bind 出发
            for kk, gg in enumerate(geoms):
                if init[kk] is not None:
                    gg["P"] = init[kk][0].copy()
            PR.pose(bones, geoms, ANIM, f)
            p = geoms[k]["P"][sel]
            c, s = p.mean(0), p.max(0) - p.min(0)
            line += "\n%-16s           f%-3d      c=(%6.2f,%6.2f,%6.2f) size=(%5.2f,%5.2f,%5.2f)" % (
                "", f, c[0], c[1], c[2], s[0], s[1], s[2])
        print(line)

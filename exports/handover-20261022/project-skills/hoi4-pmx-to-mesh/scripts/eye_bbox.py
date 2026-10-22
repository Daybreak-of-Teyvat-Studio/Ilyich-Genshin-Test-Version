# -*- coding: utf-8 -*-
"""从最终 .mesh 的 face draw call 里，按构建时的材质分段取顶点，
打印每个材质的几何包围盒 —— 直接判断「眼球层到底在哪、有没有被脸皮盖住」。"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_preview as RP                                    # noqa: E402

V = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
     r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_fix5")
MESH = os.path.join(V, "Vysna_infantry.mesh")

# 与 vysna_build 的 grp_faces 顺序一致：只累加「保留的」face 组材质
SEG = [("颜", 1942), ("颜2", 1032), ("睫", 1116), ("眉", 52),
       ("目", 192), ("鼻线", 35), ("口舌", 524), ("齿", 144)]

nodes = RP.gather(MESH)
fi = next(i for i, n in enumerate(nodes) if "face" in str(n["diff"]).lower())
nd = nodes[fi]
P, T = nd["P"], nd["T"]
print("face draw call: 顶点 %d 三角 %d" % (len(P), len(T)))
print()
print("%-6s %6s  %-26s %-26s %-22s" % ("材质", "三角", "x 范围", "y 范围", "z 范围"))
print("-" * 96)

acc = 0
boxes = {}
for nm, cnt in SEG:
    tri = T[acc:acc + cnt]
    idx = np.unique(tri.ravel())
    q = P[idx]
    boxes[nm] = (q.min(0), q.max(0), q.mean(0))
    print("%-6s %6d  [%+7.3f,%+7.3f]        [%+7.3f,%+7.3f]        [%+7.3f,%+7.3f]"
          % (nm, cnt, q[:, 0].min(), q[:, 0].max(),
             q[:, 1].min(), q[:, 1].max(), q[:, 2].min(), q[:, 2].max()))
    acc += cnt

print()
print("★ 关键对比（眼球各层 vs 脸皮/睫毛）：")
face = boxes["颜"]
for nm in ("目", "睫", "颜2"):
    lo, hi, c = boxes[nm]
    print("  %-4s 中心 (%+.3f, %+.3f, %+.3f)   相对「颜」的 z 偏移 %+.4f"
          % (nm, c[0], c[1], c[2], c[2] - face[2][2]))
print()
print("  角色朝 -Z（脸在 z 较小的一侧）= 眼睛的 z 必须比「颜」更小。")

# -*- coding: utf-8 -*-
"""测量眼球各层（白目/目/瞳/目光）与脸皮（颜/颜2）之间的深度关系。

角色朝 -Z，故 z 越小越靠前。对每个眼球顶点，取 (x,y) 邻域内的脸皮顶点，
比较两者 z，得到「眼球被脸皮挡住多少」。只读。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmx_parse import PMX  # noqa: E402

S = 0.389774
R = np.array([[1.0, 0.0, 0.0],
              [0.0, 0.9985, 0.0544],
              [0.0, -0.0544, 0.9985]])
T = np.array([0.0, -0.0614, 0.4709])

p = PMX(r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳\薇斯纳.pmx")
V = np.array(p.v_pos, np.float64)
Vh = S * (R @ V.T).T + T

cur = 0
verts_of = {}
for mi, m in enumerate(p.materials):
    n = m["face_count"]
    idx = np.array(p.faces[cur:cur + n], np.int64)
    verts_of[mi] = np.unique(idx)
    cur += n

EYE = [6, 7, 8, 9]        # 白目 目 瞳 目光
SKIN = [0, 1]             # 颜 颜2

skin = Vh[np.concatenate([verts_of[i] for i in SKIN])]

out = []
out.append("眼球层与脸皮 (x,y) 邻域内的 z 关系（角色朝 -Z，z 越小越靠前）")
out.append("正数 = 眼球在脸皮后面多少（被挡住）；负数 = 眼球已经露在脸皮前面")
out.append("=" * 96)
out.append("%-8s %6s %10s %10s %10s %10s   %s"
           % ("材质", "顶点", "P50", "P90", "P99", "max", "结论"))
out.append("-" * 96)

for mi in EYE:
    nm = p.materials[mi]["name"]
    ev = Vh[verts_of[mi]]
    gaps = []
    for e in ev:
        m = (np.abs(skin[:, 0] - e[0]) < 0.015) & (np.abs(skin[:, 1] - e[1]) < 0.015)
        if not m.any():
            continue
        gaps.append(skin[m, 2].min() - e[2])
    if not gaps:
        out.append("%-8s %6d   邻域内找不到脸皮顶点" % (nm, len(ev)))
        continue
    g = np.array(gaps)
    concl = "需要前推 > P99 才能露出来" if np.percentile(g, 99) > 0 else "已在前方"
    out.append("%-8s %6d %10.4f %10.4f %10.4f %10.4f   %s"
               % (nm, len(ev), np.percentile(g, 50), np.percentile(g, 90),
                  np.percentile(g, 99), g.max(), concl))

# 脸皮自身的相对关系
out.append("")
out.append("脸皮各层 z 统计（观察 颜 与 颜2 谁更靠前）")
for mi in [0, 1]:
    nm = p.materials[mi]["name"]
    z = Vh[verts_of[mi], 2]
    out.append("  %-6s 顶点 %5d  z: min=%8.4f mean=%8.4f max=%8.4f"
               % (nm, len(z), z.min(), z.mean(), z.max()))

# 睫毛/眉参考
out.append("")
out.append("参考：")
for mi in [4, 5]:
    nm = p.materials[mi]["name"]
    z = Vh[verts_of[mi], 2]
    out.append("  %-6s 顶点 %5d  z: min=%8.4f mean=%8.4f max=%8.4f" % (nm, len(z), z.min(), z.mean(), z.max()))

txt = "\n".join(out)
print(txt)
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_eye_depth")
path = base + ".txt"
i = 2
while os.path.exists(path):
    path = "%s_%d.txt" % (base, i)
    i += 1
open(path, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % path)

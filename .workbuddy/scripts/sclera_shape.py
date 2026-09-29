# -*- coding: utf-8 -*-
"""白目 球体的真实形状：z 对 (x,y) 的分布。判断它是半球还是整球、
前极点在哪、以及和脸皮/虹膜的关系。"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
V = np.array(pmx.v_pos, np.float64)
UV = np.array(pmx.v_uv, np.float64)
faces = np.array(pmx.faces, np.int64)

EXCLUDE = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
           "裙+", "颜3", "颜4"]
FG = {"颜", "颜2", "睫", "眉", "白目", "目", "瞳", "目光", "鼻线", "口舌",
      "齿", "星目", "照れ"}
segs = {}
acc = 0
for mt in pmx.materials:
    nm = mt["name"]
    cnt = mt["face_count"]
    if not any(k in nm for k in EXCLUDE) and nm in FG:
        segs[nm] = (acc, cnt, mt["tex"])
    acc += cnt

out = []
for nm in ["白目", "目"]:
    a, cnt, ti = segs[nm]
    f = np.unique(faces[a:a + cnt])
    X, Y, Z = V[f, 0], V[f, 1], V[f, 2]
    out.append("%s  顶点 %d" % (nm, len(f)))
    out.append("   x [%8.3f, %8.3f]  跨度 %6.3f" % (X.min(), X.max(), np.ptp(X)))
    out.append("   y [%8.3f, %8.3f]  跨度 %6.3f" % (Y.min(), Y.max(), np.ptp(Y)))
    out.append("   z [%8.3f, %8.3f]  跨度 %6.3f" % (Z.min(), Z.max(), np.ptp(Z)))
    cx, cy = (X.min() + X.max()) / 2, (Y.min() + Y.max()) / 2
    out.append("   中心 (%.3f, %.3f)  半径(x,y) ~ (%.3f, %.3f)"
               % (cx, cy, np.ptp(X) / 2, np.ptp(Y) / 2))
    # 把 x 归一化到 [-1,1] 看 z 的形状
    r = np.sqrt(((X - cx) / (np.ptp(X) / 2)) ** 2 + ((Y - cy) / (np.ptp(Y) / 2)) ** 2)
    out.append("   归一化半径 r: min %.3f P50 %.3f max %.3f" % (r.min(), np.median(r), r.max()))
    for lo, hi in [(0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.01)]:
        m = (r >= lo) & (r < hi)
        if m.any():
            out.append("     r∈[%.2f,%.2f) 顶点 %3d   z [%8.3f, %8.3f] 均值 %8.3f"
                       % (lo, hi, m.sum(), Z[m].min(), Z[m].max(), Z[m].mean()))
    out.append("")

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_sclera_shape.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_sclera_shape_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("-> %s" % p)

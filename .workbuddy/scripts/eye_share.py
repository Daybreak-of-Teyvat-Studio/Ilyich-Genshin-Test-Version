# -*- coding: utf-8 -*-
"""核对：face 组里 白目 的三角是否真的复用 颜 的顶点号（导致去重后 UV 被并）。

直接解析 PMX 面表：统计 face 组各材质的三角用到的顶点号，
看 白目/目 与 颜/颜2/睫 的顶点集合是否相交。
"""
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pmx_parse import PMX                      # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
faces = np.array(pmx.faces, np.int64)

EXCLUDE = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
           "裙+", "颜3", "颜4"]
FG = {"颜", "颜2", "睫", "眉", "白目", "目", "瞳", "目光", "鼻线", "口舌",
      "齿", "星目", "照れ"}

verts = {}
acc = 0
for mt in pmx.materials:
    nm = mt["name"]
    cnt = mt["face_count"]
    if not any(k in nm for k in EXCLUDE) and nm in FG:
        T = faces[acc:acc + cnt]
        verts[nm] = set(int(x) for x in np.unique(T))
    acc += cnt

names = [n for n in ["颜", "颜2", "睫", "眉", "白目", "目", "瞳", "目光", "星目"]
         if n in verts]
out = []
out.append("face 组各材质的顶点集合大小与两两交集")
out.append("=" * 78)
for n in names:
    out.append("  %-5s 顶点 %5d" % (n, len(verts[n])))
out.append("")
out.append("两两交集（非空 = 有共享顶点 -> 按顶点去重会把两层并到一起）")
out.append("-" * 78)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        A, B = names[i], names[j]
        inter = verts[A] & verts[B]
        if inter:
            out.append("  %-5s ∩ %-5s = %5d 个共享顶点  (占 %s 的 %.1f%%)"
                       % (A, B, len(inter), A, len(inter) / len(verts[A]) * 100))
        else:
            out.append("  %-5s ∩ %-5s = 0（无共享）" % (A, B))

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_eye_share.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_eye_share_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % p)

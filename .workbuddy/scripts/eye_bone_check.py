# -*- coding: utf-8 -*-
"""检查眼球材质 / 脸皮材质各自绑定在哪些骨上 —— 若不同，bind conform 会把它们错开。"""
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pmx_parse import PMX                                       # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
F = np.array(pmx.faces, np.int64).reshape(-1)

segs, acc = {}, 0
for m in pmx.materials:
    segs.setdefault(m["name"], (acc, m["face_count"] // 3))
    acc += m["face_count"] // 3


def verts_of(nm):
    a, c = segs[nm]
    return np.unique(F[3 * a:3 * (a + c)])


print("含「目 / 眼 / 瞳」的骨名与位置：")
for i, b in enumerate(pmx.bones):
    if any(k in b["name"] for k in ("目", "眼", "瞳")):
        print("   #%-4d %-14s pos=(%+.3f, %+.3f, %+.3f) parent=%s"
              % (i, b["name"], b["pos"][0], b["pos"][1], b["pos"][2],
                 pmx.bones[b["parent"]]["name"] if b["parent"] >= 0 else "-"))

print()
print("%-5s %6s  绑定的骨（权重>0.1 的顶点计数）" % ("材质", "顶点"))
for nm in ("颜", "颜2", "睫", "眉", "目", "鼻线", "口舌"):
    v = verts_of(nm)
    c = Counter()
    for k in v:
        for b, w in zip(pmx.v_wbone[k], pmx.v_wweight[k]):
            if w > 0.1:
                c[pmx.bones[b]["name"]] += 1
    print("%-5s %6d  %s" % (nm, len(v), c.most_common(6)))

print()
print("★ 若「目」的主导骨与「颜/睫」不同，conform 会给它们不同的位移，眼睛就会陷进脸里。")

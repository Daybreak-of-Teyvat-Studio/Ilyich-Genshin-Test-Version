# -*- coding: utf-8 -*-
"""几何硬数据：白目 / 目 / 瞳 各自的前表面在主视线（+Z 方向）上的位置。

做法：把每层的顶点按 (x, y) 分格（0.01 单位），取每格里 z 最小（最靠前）的值，
然后比较三层在「同一 (x,y) 格子」的前表面 z，看谁在前面。
这样比"整体 z 中位数"精确得多 —— 中位数会被眼球后方顶点带偏。
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402
from pdx_data import read_meshfile             # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
V9 = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
      r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out10")

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
EXCLUDE = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
           "裙+", "颜3", "颜4"]
FG = {"颜", "颜2", "睫", "眉", "白目", "目", "瞳", "目光", "鼻线", "口舌",
      "齿", "星目", "照れ"}
seq = []
for mt in pmx.materials:
    nm = mt["name"]
    if any(k in nm for k in EXCLUDE) or nm not in FG:
        continue
    seq.append((nm, mt["face_count"] // 3))
tot = sum(n for _, n in seq)

root = read_meshfile(os.path.join(V9, "Vysna_infantry.mesh"))
FACE = None
for o in root:
    for sh in o:
        for m in sh.findall("mesh"):
            if "p" in m.attrib and len(np.array(m.get("tri"))) // 3 == tot:
                FACE = m
P = np.array(FACE.get("p"), np.float64).reshape(-1, 3)
T = np.array(FACE.get("tri"), np.int64).reshape(-1, 3)

out = []
out.append("各层前表面 z（每 0.02 单位 (x,y) 栅格里取最小 z；z 越小越靠前）")
out.append("=" * 84)
cur = 0
front = {}
for nm, n in seq:
    idx = np.unique(T[cur:cur + n].ravel())
    V = P[idx]
    key = (np.round(V[:, 0] / 0.02).astype(np.int64),
           np.round(V[:, 1] / 0.02).astype(np.int64))
    d = {}
    for k, z in zip(key, V[:, 2]):
        kk = (int(k[0]), int(k[1]))
        if kk not in d or z < d[kk]:
            d[kk] = z
    front[nm] = d
    zs = np.array(list(d.values()))
    out.append("  %-4s 前表面 z: min %8.5f  P10 %8.5f  P50 %8.5f"
               % (nm, zs.min(), np.percentile(zs, 10), np.percentile(zs, 50)))
    cur += n

# 比对：白目 与 目 落在同一 (x,y) 格时，谁靠前
out.append("")
out.append("同一 (x,y) 栅格上，各层相对 白目 的前后关系（负 = 该层在白目前面）")
out.append("-" * 84)
sb = front["白目"]
for nm in ["目", "瞳", "目光"]:
    if nm not in front:
        continue
    o = front[nm]
    common = sorted(set(sb) & set(o))
    if not common:
        out.append("  %-4s 与 白目 没有共同栅格" % nm)
        continue
    dz = np.array([o[k] - sb[k] for k in common])
    out.append("  %-4s 共同栅格 %5d   目_白目: min %8.5f  P10 %8.5f  P50 %8.5f  max %8.5f"
               % (nm, len(common), dz.min(), np.percentile(dz, 10),
                  np.percentile(dz, 50), dz.max()))
    out.append("       白目 在该层前面的格子数 = %d (%.2f%%)"
               % ((dz > 0).sum(), (dz > 0).mean() * 100))

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_eye_front.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_eye_front_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % p)

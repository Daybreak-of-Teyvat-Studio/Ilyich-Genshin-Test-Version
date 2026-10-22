# -*- coding: utf-8 -*-
"""用「三角形质心集合」找出 PMX 里所有真正重合的面（含部分重合），
不限材质索引数是否相等。用于消除 z-fighting 隐患。只读。"""
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmx_parse import PMX  # noqa: E402

PMX_PATH = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳\薇斯纳.pmx"
EXCLUDE = ["结晶", "头饰"]     # 只关心保留下来的材质

p = PMX(PMX_PATH)
V = np.array(p.v_pos, np.float64)
F = np.array(p.faces, np.int64)

cen = (V[F[0::3]] + V[F[1::3]] + V[F[2::3]]) / 3.0
cen_r = np.round(cen, 3)

mat_of_tri = np.empty(len(cen), np.int64)
cur = 0
for mi, m in enumerate(p.materials):
    n = m["face_count"] // 3
    mat_of_tri[cur:cur + n] = mi
    cur += n

keep = [i for i, m in enumerate(p.materials)
        if not any(k in m["name"] for k in EXCLUDE)]

# 每个材质的质心字符串集合 + 反查
sets = {}
for mi in keep:
    idx = np.nonzero(mat_of_tri == mi)[0]
    sets[mi] = set(map(tuple, cen_r[idx]))

out = []
out.append("材质 %d 个（保留 %d 个）" % (len(p.materials), len(keep)))
out.append("三角形质心重合检测（坐标取整到 1e-3）")
out.append("=" * 112)

pairs = []
for a in keep:
    for b in keep:
        if b <= a:
            continue
        A, B = sets[a], sets[b]
        inter = len(A & B)
        if inter < 20:
            continue
        ratio = inter / float(min(len(A), len(B)))
        if ratio >= 0.15:
            pairs.append((ratio, inter, a, b))

pairs.sort(reverse=True)
if not pairs:
    out.append("  未发现明显重合的材质对")
for ratio, inter, a, b in pairs:
    na, nb = p.materials[a]["name"], p.materials[b]["name"]
    ta = os.path.basename(p.textures[p.materials[a]["tex"]]) if p.materials[a]["tex"] >= 0 else "-"
    tb = os.path.basename(p.textures[p.materials[b]["tex"]]) if p.materials[b]["tex"] >= 0 else "-"
    out.append("  重合率 %5.1f%%  共同三角 %6d   idx%-3d %-8s(%-14s)  vs  idx%-3d %-8s(%-14s)   [三角 %d vs %d]"
               % (ratio * 100, inter, a, na, ta, b, nb, tb, len(sets[a]), len(sets[b])))

# 每个材质「被更靠前的材质完全盖住」的统计：质心反查谁在最后
out.append("")
out.append("按材质顺序看：同一位置若有多个材质，后画的（<=规则）与先画的（<规则）分别是谁")
out.append("-" * 112)
from collections import defaultdict as dd
pos2mats = dd(list)
for mi in keep:
    for c in sets[mi]:
        pos2mats[c].append(mi)
conf = [c for c, ms in pos2mats.items() if len(ms) > 1]
out.append("  有 %d 个位置被 2 个以上材质同时占用（共 %d 个占用位置）" % (len(conf), len(pos2mats)))

# 统计冲突里「先画 vs 后画」的材质组合
combo = dd(int)
for c in conf:
    ms = sorted(pos2mats[c])
    combo[(p.materials[ms[0]]["name"], p.materials[ms[-1]]["name"])] += 1
top = sorted(combo.items(), key=lambda kv: -kv[1])[:25]
out.append("  冲突最多的组合（前者=先画，后者=后画）：")
for (n1, n2), cnt in top:
    out.append("      %-8s → %-8s  %6d 个三角位置" % (n1, n2, cnt))

txt = "\n".join(out)
print(txt)
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_coincident")
path = base + ".txt"
i = 2
while os.path.exists(path):
    path = "%s_%d.txt" % (base, i)
    i += 1
open(path, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % path)

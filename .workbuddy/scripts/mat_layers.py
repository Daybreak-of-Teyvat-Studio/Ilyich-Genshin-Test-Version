# -*- coding: utf-8 -*-
"""逐个 PMX 材质测量：索引数、顶点位置均值/极值、UV 范围。
目的是找出「几何完全重合」的叠层材质组，并判断谁在谁前面（角色朝 -Z）。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pmx_parse  # noqa: E402

PMX = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳\薇斯纳.pmx"

p = pmx_parse.PMX(PMX)
V = np.array(p.v_pos, np.float64)
UV = np.array(p.v_uv, np.float64)
faces = np.array(p.faces, np.int64)
mats = p.materials
texs = p.textures
print("材质字典键:", sorted(mats[0].keys()))

out = []
out.append("顶点 %d  索引 %d  材质 %d" % (len(V), len(faces), len(mats)))
out.append("")
out.append("%-4s %-8s %-22s %8s %9s %9s %9s   %s"
           % ("idx", "name", "tex", "index数", "meanX", "meanY", "meanZ", "UV范围"))
out.append("-" * 122)

rows = []
_cursor = 0
for i, m in enumerate(mats):
    # 材质只记 face_count（索引数），偏移由前面材质累加得到
    s = _cursor
    n = m["face_count"]
    _cursor += n
    idx = faces[s:s + n]
    pos = V[idx]
    uv = UV[idx]
    tex = texs[m["tex"]] if 0 <= m["tex"] < len(texs) else "-"
    tex = os.path.basename(tex) if tex != "-" else "-"
    rows.append(dict(
        i=i, name=m["name"], tex=tex, n=n,
        mean=pos.mean(0), mn=pos.min(0), mx=pos.max(0),
        uv_min=uv.min(0), uv_max=uv.max(0),
        verts=pos,
    ))
    out.append("%-4d %-8s %-22s %8d %9.4f %9.4f %9.4f   u[%.3f,%.3f] v[%.3f,%.3f]"
               % (i, m["name"], tex, n,
                  pos[:, 0].mean(), pos[:, 1].mean(), pos[:, 2].mean(),
                  uv[:, 0].min(), uv[:, 0].max(), uv[:, 1].min(), uv[:, 1].max()))

# ---- 找完全重合的材质组 ----
out.append("")
out.append("=" * 122)
out.append("几何完全重合的材质组（顶点集合逐点最大距离 < 1e-4）")
out.append("=" * 122)


def coincident(a, b):
    if len(a["verts"]) != len(b["verts"]):
        return None
    d = np.abs(a["verts"] - b["verts"]).max()
    return d


used = set()
groups = []
for a in rows:
    if a["i"] in used:
        continue
    grp = [a]
    for b in rows:
        if b["i"] == a["i"] or b["i"] in used:
            continue
        d = coincident(a, b)
        if d is not None and d < 1e-4:
            grp.append(b)
    if len(grp) > 1:
        for g in grp:
            used.add(g["i"])
        groups.append(grp)

if not groups:
    out.append("  未发现完全重合的材质组")
for grp in groups:
    out.append("")
    out.append("  组（%d 个材质，几何逐点重合）：" % len(grp))
    for g in grp:
        out.append("      idx %-3d %-8s tex=%-16s 面索引 %6d  meanZ=%.5f  uv u[%.3f,%.3f] v[%.3f,%.3f]"
                   % (g["i"], g["name"], g["tex"], g["n"], g["mean"][2],
                      g["uv_min"][0], g["uv_max"][0], g["uv_min"][1], g["uv_max"][1]))

txt = "\n".join(out)
print(txt)
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_mat_layers")
path = base + ".txt"
i = 2
while os.path.exists(path):
    path = "%s_%d.txt" % (base, i)
    i += 1
with open(path, "w", encoding="utf-8") as f:
    f.write(txt + "\n")
print("\n-> %s" % path)

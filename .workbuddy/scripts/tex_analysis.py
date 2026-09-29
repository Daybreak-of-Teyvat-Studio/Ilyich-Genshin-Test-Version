# -*- coding: utf-8 -*-
"""分析 薇斯纳.pmx：贴图清单、每材质 UV 范围、贴图尺寸。
输出 .workbuddy/scripts/report_tex_analysis.txt
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmx_parse import PMX  # noqa

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_tex_analysis.txt")

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
L = []
P = L.append

P("贴图清单（%d）：" % len(pmx.textures))
for i, t in enumerate(pmx.textures):
    full = os.path.join(SRC, t.replace("/", os.sep))
    dim = ""
    if os.path.isfile(full):
        try:
            with Image.open(full) as im:
                dim = "%dx%d %s %dKB" % (im.width, im.height, im.mode,
                                         os.path.getsize(full) // 1024)
        except Exception as e:
            dim = "读图失败 %s" % e
    else:
        dim = "文件不存在"
    P("  [%2d] %-24s %s" % (i, t, dim))

# UV 范围：按材质的面区间统计
UV = np.array(pmx.v_uv, dtype=np.float64)
faces = pmx.faces
P("")
P("每材质 UV 范围（u/v 是否落在 [0,1]）：")
P("  %-8s %-22s %-6s %-6s %-8s   %s" % ("idx", "name", "tex", "sphere", "面数", "UV u:[..] v:[..]"))
acc = 0
allins = True
for i, mt in enumerate(pmx.materials):
    st, cnt = acc, mt["face_count"]
    acc += cnt
    vids = np.unique(np.array(faces[st:st + cnt], dtype=np.int64)) if cnt else np.array([], dtype=np.int64)
    if len(vids):
        u = UV[vids]
    else:
        u = np.zeros((1, 2))
    ins = (u.min() >= -0.02) and (u.max() <= 1.02)
    allins = allins and ins
    P("  %-8d %-22s %-6s %-6s %-8d   u:[%6.3f,%6.3f] v:[%6.3f,%6.3f]  %s" % (
        i, mt["name"], mt["tex"], mt["sphere"], cnt,
        u[:, 0].min(), u[:, 0].max(), u[:, 1].min(), u[:, 1].max(),
        "" if ins else "  <== 超出"))

P("")
P("全局 UV 范围: u[%.4f, %.4f]  v[%.4f, %.4f]" % (
    UV[:, 0].min(), UV[:, 0].max(), UV[:, 1].min(), UV[:, 1].max()))
P("所有材质 UV 都在 [0,1] 内？ %s" % allins)

# 按贴图归并统计
P("")
P("按贴图归并（同贴图的材质可共用一份材质）：")
by_tex = {}
acc = 0
for i, mt in enumerate(pmx.materials):
    by_tex.setdefault(mt["tex"], []).append(mt["name"])
    acc += mt["face_count"]
for k in sorted(by_tex):
    nm = pmx.textures[k] if 0 <= k < len(pmx.textures) else "?"
    P("  tex[%2d] %-22s <- %s" % (k, nm, ", ".join(by_tex[k])))

txt = "\n".join(L)
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)

# -*- coding: utf-8 -*-
"""列出 face 组各材质的贴图 / draw_flag / 面数 / 是否被剔除。"""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pmx_parse  # noqa

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳\薇斯纳.pmx"

EXCLUDE = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s", "裙+", "颜3", "颜4"]

p = pmx_parse.PMX(SRC)
lines = []
lines.append("材质序号  名称       贴图           draw_flag  面数    剔除?")
lines.append("=" * 78)
tex = p.textures
for i, m in enumerate(p.materials):
    nm = m["name"]
    ti = m["tex"]
    tn = tex[ti] if 0 <= ti < len(tex) else "(none)"
    tn = tn.replace("\\", "/")
    flag = m.get("draw_flag", -1)
    excl = any(k in nm for k in EXCLUDE)
    lines.append("%3d  %-10s %-24s 0x%02x      %6d  %s"
                 % (i, nm, tn, flag, m["face_count"], "剔除" if excl else ""))

out = os.path.join(HERE, "report_face_mats.txt")
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
print("\n->", out)

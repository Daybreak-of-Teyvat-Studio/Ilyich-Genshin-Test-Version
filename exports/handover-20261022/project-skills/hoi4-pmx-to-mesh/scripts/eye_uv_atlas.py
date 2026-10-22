# -*- coding: utf-8 -*-
"""把 mesh 里 face 组各材质的 UV 包围盒画回 face 图集，
用「颜」（脸皮）当标尺判断 UV 是否正确指向对应贴图的 cell。"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_preview as RP                                    # noqa: E402

V = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
     r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_fix5")
MESH = os.path.join(V, "Vysna_infantry.mesh")
ATLAS = Image.open(os.path.join(V, "vysna_face_diffuse.dds")).convert("RGBA")
AW, AH = ATLAS.size
print("atlas", ATLAS.size)

SEG = [("颜", 1942), ("颜2", 1032), ("睫", 1116), ("眉", 52),
       ("目", 192), ("鼻线", 35), ("口舌", 524), ("齿", 144)]

nodes = RP.gather(MESH)
fi = next(i for i, n in enumerate(nodes) if "face" in str(n["diff"]).lower())
nd = nodes[fi]
T, UV = nd["T"], nd["UV"]
print("face UV shape", UV.shape)

base = ATLAS.copy()
d = ImageDraw.Draw(base)
COL = {"颜": (255, 0, 0), "颜2": (255, 140, 0), "睫": (0, 255, 0),
       "眉": (0, 200, 255), "目": (255, 0, 255), "鼻线": (255, 255, 0),
       "口舌": (255, 255, 255), "齿": (0, 255, 255)}

acc = 0
print()
print("%-6s  u 范围                 v 范围                像素 bbox (v→y 向下)")
for nm, cnt in SEG:
    tri = T[acc:acc + cnt]
    idx = np.unique(tri.ravel())
    uv = UV[idx]
    u0, u1 = uv[:, 0].min(), uv[:, 0].max()
    v0, v1 = uv[:, 1].min(), uv[:, 1].max()
    x0, x1 = u0 * AW, u1 * AW
    y0, y1 = v0 * AH, v1 * AH
    print("%-6s  [%.4f, %.4f]   [%.4f, %.4f]   x[%.0f,%.0f] y[%.0f,%.0f]"
          % (nm, u0, u1, v0, v1, x0, x1, y0, y1))
    d.rectangle([x0, y0, x1, y1], outline=COL[nm], width=4)
    d.text((x0 + 6, y0 + 6), nm.encode("ascii", "replace").decode(), fill=COL[nm])
    acc += cnt

p = os.path.join(HERE, "report_uv_atlas.png")
base.convert("RGB").resize((AW // 2, AH // 2)).save(p)
print("\n-> %s" % p)

# -*- coding: utf-8 -*-
"""直接检查 v4 图集：把 face 图集里 目/瞳/眼白 三个 cell 抠出来放大存图，
并统计图集「不该有不透明像素」的区域（gutter 是否真透明）。"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
V4 = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
      r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out4")
OUT = os.path.join(V4, "_atlascheck")
os.makedirs(OUT, exist_ok=True)

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))

# 源贴图：目 / 瞳 / 目光 的可见率与均值
print("源贴图：")
for nm, f in [("目", "tex/目.png"), ("瞳", "tex/瞳.png"), ("目光", "tex/目光.png")]:
    p = os.path.join(SRC, f)
    im = Image.open(p).convert("RGBA")
    a = np.asarray(im, np.uint8)
    vis = a[..., 3] > 128
    rgb = a[..., :3]
    print("   %-4s %-12s %4dx%-4d 不透明 %5.1f%%  全图均值 %s  不透明区均值 %s"
          % (nm, f, im.width, im.height, vis.mean() * 100,
             tuple(int(x) for x in rgb.mean((0, 1))),
             tuple(int(x) for x in rgb[vis].mean(0)) if vis.any() else "-"))

# 图集 PNG
ap = os.path.join(V4, "vysna_face_atlas.png")
at = np.asarray(Image.open(ap).convert("RGBA"), np.uint8)
print("\n图集 %s  %dx%d" % (ap, at.shape[1], at.shape[0]))
print("   整张不透明占比 %.1f%%" % ((at[..., 3] > 128).mean() * 100))

# 把图集左上 1600x1120（=放置区）抠出来放大
crop = at[:1120, :1600]
Image.fromarray(crop).save(os.path.join(OUT, "atlas_face_cells.png"))
print("   -> %s" % os.path.join(OUT, "atlas_face_cells.png"))

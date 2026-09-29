# -*- coding: utf-8 -*-
"""把 face 组按材质逐个单独渲染，输出拼图，定位到底哪一层能显示出来。"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402
import render_preview as RP                    # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
V8 = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
      r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out8")
MESH = os.path.join(V8, "Vysna_infantry.mesh")
OUT = os.path.join(V8, "_eyetest")
os.makedirs(OUT, exist_ok=True)

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

nodes = RP.gather(MESH)
face_i = [i for i, n in enumerate(nodes) if len(n["T"]) == tot][0]
FACE = nodes[face_i]

W, H, ZOOM, FY = 900, 900, 14.0, 6.58
import math                                          # noqa: E402
allP = np.concatenate([n["P"] for n in nodes], 0)
C = np.array([allP[:, 0].mean(), FY, allP[:, 2].mean()])
RAD = np.linalg.norm(allP - C, axis=1).max()
SCALE = min(W, H) / (2.0 * RAD * 1.05) * ZOOM
az, el = RP.VIEWS["front"]
fwd = np.array([math.cos(az) * math.cos(el), math.sin(el), math.sin(az) * math.cos(el)])
fwd /= np.linalg.norm(fwd)
right = np.cross(fwd, np.array([0.0, 1.0, 0.0]))
right /= np.linalg.norm(right)
up = np.cross(right, fwd)
# 用 白目 的几何中心定框
acc = 0
scl = None
for nm, n in seq:
    if nm == "白目":
        scl = (acc, acc + n)
    acc += n
ev = np.unique(FACE["T"][scl[0]:scl[1]].ravel())
EC = FACE["P"][ev].mean(0)
rel = EC - C
PX = W / 2 + (rel @ right) * SCALE
PY = H / 2 - (rel @ up) * SCALE
hw, hh = int(0.20 * SCALE), int(0.15 * SCALE)
BOX = (max(0, int(PX - hw)), max(0, int(PY - hh)),
       min(W, int(PX + hw)), min(H, int(PY + hh)))
print("scale=%.1f  白目中心像素 (%.0f,%.0f)  BOX=%s" % (SCALE, PX, PY, BOX))


def only(nm):
    start = None
    for k, n in seq:
        if k == nm:
            break
        start = (start or 0) + n
    start = start or 0
    n = dict(seq)[nm]
    idx = np.arange(start, start + n)
    out = []
    for i, nd in enumerate(nodes):
        if i != face_i:
            out.append(nd)
            continue
        d = dict(nd)
        d["T"] = nd["T"][idx]
        out.append(d)
    return out


CASES = ["白目", "目", "瞳", "目光", "颜", "睫"]
imgs = []
for nm in CASES:
    a = RP.render(only(nm), V8, W, H, RP.VIEWS["front"], zoom=ZOOM, focus_y=FY,
                  cull=False)
    im = Image.fromarray(a).crop(BOX)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 160, 18], fill=(0, 0, 0))
    d.text((4, 4), nm, fill=(255, 235, 120))
    imgs.append(im)
    print("  已渲染 %s" % nm)
sheet = np.concatenate([np.asarray(i) for i in imgs], axis=1)
p = RP.fresh(os.path.join(OUT, "EYE_EACH.png"))
Image.fromarray(sheet).save(p)
print("-> %s (%dx%d)" % (p, sheet.shape[1], sheet.shape[0]))

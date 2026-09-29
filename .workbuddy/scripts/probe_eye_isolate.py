# -*- coding: utf-8 -*-
"""隔离渲染：把输出 mesh 的 face 节点按材质区间切片，单独画眼球三角，
确认「眼球几何是否存在、是否被脸皮遮挡」。

输出三角在 tri 数组里的排列 = 材质索引顺序（vysna_build 按材质顺序追加）。
face 组各材质三角数（来自 PMX，/3）：
  颜1942 颜2 1032 睫1116 眉52 白目148 目192 瞳192 目光200 鼻线35 口舌524 齿144 星目28 = 5605
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_preview as RP  # noqa: E402

MESH = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out3\Vysna_infantry.mesh")

SEG = [("颜", 1942), ("颜2", 1032), ("睫", 1116), ("眉", 52), ("白目", 148),
       ("目", 192), ("瞳", 192), ("目光", 200), ("鼻线", 35), ("口舌", 524),
       ("齿", 144), ("星目", 28)]

acc = 0
bounds = {}
for nm, c in SEG:
    bounds[nm] = (acc, acc + c)
    acc += c
print("face 三角总数 = %d" % acc)

nodes = RP.gather(MESH)
print("mesh 节点 %d，各节点三角: %s" % (len(nodes), [len(n["T"]) for n in nodes]))
face_i = 1
face = nodes[face_i]
assert len(face["T"]) == acc, "face 三角数不符：%d vs %d" % (len(face["T"]), acc)

EYE = ["白目", "目", "瞳", "目光", "星目", "鼻线"]
eye_idx = np.concatenate([np.arange(*bounds[n]) for n in EYE])
rest_idx = np.setdiff1d(np.arange(acc), eye_idx)

VIEW = RP.VIEWS["front"]
W, H, ZOOM, FY = 620, 560, 7.0, 6.58


def mk(tri_idx):
    """保留全部 mesh 节点（相机的尺度由所有顶点包围球决定，少传节点会把画面放大错位），
    只替换 face 节点的三角列表。"""
    out = []
    for i, n in enumerate(nodes):
        if i != face_i:
            out.append(n)
            continue
        d = dict(n)
        d["T"] = n["T"][tri_idx]
        out.append(d)
    return out


panels = [
    ("(a) only eyes", mk(eye_idx)),
    ("(b) face WITHOUT eyes", mk(rest_idx)),
    ("(c) all face", mk(np.arange(acc))),
]
imgs = []
for cap, ns in panels:
    a = RP.render(ns, os.path.dirname(MESH), W, H, VIEW, zoom=ZOOM, focus_y=FY,
                  cull=False)
    im = Image.fromarray(a)
    ImageDraw.Draw(im).rectangle([0, 0, 190, 20], fill=(0, 0, 0))
    ImageDraw.Draw(im).text((5, 5), cap, fill=(255, 235, 120))
    imgs.append(im)

cv = Image.new("RGB", (W * 3 + 8, H), (12, 12, 12))
for i, im in enumerate(imgs):
    cv.paste(im, (i * (W + 4), 0))
out = RP.fresh(os.path.abspath(os.path.join(HERE, "..", "vysna_out3", "PROBE_eye_isolate.png")))
cv.save(out)
print("-> %s %s" % (out, cv.size))

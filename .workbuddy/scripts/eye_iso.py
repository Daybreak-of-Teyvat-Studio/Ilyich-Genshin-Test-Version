# -*- coding: utf-8 -*-
"""逐层渲染 face 组（fix5），用构建时的真实材质分段，定位眼球被谁挡住。"""
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
OUT = os.path.join(V, "_eyetest")
os.makedirs(OUT, exist_ok=True)

W, H, ZOOM, FY = 460, 460, 5.5, 6.72

SEG = [("颜", 1942), ("颜2", 1032), ("睫", 1116), ("眉", 52),
       ("目", 192), ("鼻线", 35), ("口舌", 524), ("齿", 144)]

nodes = RP.gather(MESH)
fi = next(i for i, n in enumerate(nodes) if "face" in str(n["diff"]).lower())
nd = nodes[fi]
T = nd["T"]

seg2 = {}
a = 0
for nm, c in SEG:
    seg2[nm] = (a, c)
    a += c
assert a == len(T), "分段不匹配: %d vs %d" % (a, len(T))


def run(keep, tag):
    nd2 = dict(nd)
    m = np.zeros(len(T), bool)
    for nm in keep:
        s, c = seg2[nm]
        m[s:s + c] = True
    nd2["T"] = T[m]
    img = RP.render([nd2], V, W, H, RP.VIEWS["front"],
                    zoom=ZOOM, focus_y=FY, cull=False)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 380, 18], fill=(0, 0, 0))
    d.text((4, 3), "%s  (%d tri)" % (tag, int(m.sum())), fill=(255, 235, 120))
    im.save(os.path.join(OUT, "L_%s.png" % tag.replace("+", "_")))
    return im


ALL = [n for n, _ in SEG]
sets = [
    ("ALL", ALL),
    ("face_only", ["颜", "颜2"]),
    ("only_jie", ["睫"]),
    ("only_mu", ["目"]),
    ("mu+jie", ["目", "睫"]),
    ("mu+jie+face", ["目", "睫", "颜", "颜2"]),
]
tiles = [run(k, t) for t, k in sets]

cols = 3
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (W * cols, H * rows), (24, 24, 28))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * W, (i // cols) * H))
p = os.path.join(V, "preview_LAYER_sheet.png")
sheet.save(p)
print("-> %s" % p)

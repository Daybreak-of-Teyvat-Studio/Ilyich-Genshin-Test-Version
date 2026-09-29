# -*- coding: utf-8 -*-
"""只保留 颜/颜2/睫 + 目，扫描「目」的前推量，找出能稳定显示的值。"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_preview as RP  # noqa

V = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out12"
MESH = os.path.join(V, "Vysna_infantry.mesh")
OUT = os.path.join(V, "_eyetest")
os.makedirs(OUT, exist_ok=True)

W, H, ZOOM, FY = 700, 760, 15.0, 6.72

nodes = RP.gather(MESH)
fi = next(i for i, n in enumerate(nodes) if "face" in str(n["diff"]).lower())
nd = nodes[fi]
P, T = nd["P"], nd["T"]

SEG = {"颜": (0, 1942), "颜2": (1942, 1032), "睫": (2974, 1116), "眉": (4090, 52),
       "白目": (4142, 148), "目": (4290, 192), "瞳": (4482, 192),
       "目光": (4674, 200), "鼻线": (4874, 35), "口舌": (4909, 524),
       "齿": (5433, 144), "星目": (5577, 28)}

KEEP = ["颜", "颜2", "睫", "眉", "鼻线", "口舌", "齿", "目"]


def panel(delta, depth_le):
    nd2 = dict(nd)
    keep = np.zeros(len(T), bool)
    for nm in KEEP:
        a, n = SEG[nm]
        keep[a:a + n] = True
    T2 = T[keep].copy()

    P2 = P.copy()
    if delta:
        a, n = SEG["目"]
        vids = np.unique(T[a:a + n].ravel())
        P2 = P.copy()
        P2[vids] = P[vids]
        P2[vids, 2] -= delta
    nd2["T"] = T2
    nd2["P"] = P2
    return list(nodes[:fi]) + [nd2] + list(nodes[fi + 1:])


DELTAS = [0.000, 0.010, 0.020, 0.030, 0.045, 0.060]
rows = []
for le in (False, True):
    tiles = []
    for d in DELTAS:
        img = RP.render(panel(d, le), V, W, H, RP.VIEWS["front"],
                        zoom=ZOOM, focus_y=FY, depth_le=le, cull=True)
        im = Image.fromarray(img)
        imd = ImageDraw.Draw(im)
        imd.rectangle([0, 0, 200, 18], fill=(0, 0, 0))
        imd.text((4, 4), "push=%.3f le=%d" % (d, le), fill=(255, 235, 120))
        tiles.append(im)
        print("  渲染 push=%.3f depth_le=%s" % (d, le))
    rows.append(np.concatenate(tiles, axis=1))

sheet = np.concatenate(rows, axis=0)
p = os.path.join(OUT, "EYE_PUSH2.png")
Image.fromarray(sheet).save(p)
# 同时逐格单独存
for i, le in enumerate((False, True)):
    for j, d in enumerate(DELTAS):
        a = sheet[i * H:(i + 1) * H, j * W:(j + 1) * W]
        Image.fromarray(a).save(os.path.join(OUT, "PUSH2_le%d_%03d.png" % (le, int(d * 1000))))
print("->", p, sheet.shape)

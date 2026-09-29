# -*- coding: utf-8 -*-
"""逐层消去法确认：眼睛到底被哪一层挡住。

思路：从「全脸」出发，每次只去掉一个可疑层，看眼睛出现没。
如果去掉某层后眼睛出现 => 责任就是那一层。

只读。输出 PNG 到 vysna_out5/_eyetest/。
"""
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
V3 = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
      r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out5")
MESH = os.path.join(V3, "Vysna_infantry.mesh")
OUT = os.path.join(V3, "_eyetest")

EXCLUDE_KEYS = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
                "裙+", "颜3", "颜4"]
MAT_GROUP = {
    "颜": "face", "颜2": "face", "颜3": "face", "颜4": "face", "睫": "face",
    "眉": "face", "白目": "face", "目": "face", "瞳": "face", "目光": "face",
    "鼻线": "face", "口舌": "face", "齿": "face", "星目": "face", "照れ": "face",
}

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
segs = []
out_tri = 0
for mt in pmx.materials:
    nm = mt["name"]
    cnt = mt["face_count"] // 3
    if any(k in nm for k in EXCLUDE_KEYS) or MAT_GROUP.get(nm) != "face":
        continue
    segs.append((nm, out_tri, cnt))
    out_tri += cnt

nodes = RP.gather(MESH)
face_i = [i for i, n in enumerate(nodes) if len(n["T"]) == out_tri][0]
FACE = nodes[face_i]

SEG = {nm: (a, a + n) for nm, a, n in segs}


def drop(names):
    """全脸去掉 names 里的层。"""
    keep = []
    for nm, a, n in segs:
        if nm in names:
            continue
        keep.append(np.arange(a, a + n))
    return np.concatenate(keep) if keep else np.array([], np.int64)


def only(names):
    if not names:
        return np.array([], np.int64)
    return np.concatenate([np.arange(*SEG[n]) for n in names])


def panel(tri_idx):
    out = []
    for i, n in enumerate(nodes):
        if i != face_i:
            out.append(n)
            continue
        d = dict(n)
        d["T"] = n["T"][tri_idx]
        out.append(d)
    return out


# 取景：同 probe_eye_isolate
W, H, ZOOM, FY = 1400, 1400, 14.0, 6.58
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
eye_v = np.unique(np.concatenate(
    [FACE["T"][a:b].ravel() for nm, (a, b) in SEG.items()
     if nm in ("白目", "目", "瞳", "目光", "星目")]))
EYE_C = FACE["P"][eye_v].mean(0)
rel = EYE_C - C
PX = W / 2 + (rel @ right) * SCALE
PY = H / 2 - (rel @ up) * SCALE
hw, hh = int(0.22 * SCALE), int(0.14 * SCALE)
BOX = (int(PX - hw), int(PY - hh), int(PX + hw), int(PY + hh))
print("scale=%.1f  眼心像素 (%.0f,%.0f)  裁剪框 %s (%dx%d)"
      % (SCALE, PX, PY, BOX, BOX[2] - BOX[0], BOX[3] - BOX[1]))

CASES = [
    ("0 all face", np.arange(out_tri)),
    ("1 drop 颜", drop(["颜"])),
    ("2 drop 颜2", drop(["颜2"])),
    ("3 drop 睫", drop(["睫"])),
    ("4 drop 白目", drop(["白目"])),
    ("5 drop 颜+颜2", drop(["颜", "颜2"])),
    ("6 drop 白目+颜2", drop(["白目", "颜2"])),
    ("7 eyes only", only(["白目", "目", "瞳", "目光", "星目"])),
]
imgs = []
for cap, ti in CASES:
    a = RP.render(panel(ti), V3, W, H, RP.VIEWS["front"], zoom=ZOOM, focus_y=FY,
                  cull=False)
    im = Image.fromarray(a).crop(BOX)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 300, 18], fill=(0, 0, 0))
    d.text((4, 4), cap, fill=(255, 235, 120))
    imgs.append(im)
    print("  面板 %s" % cap)

sheet = np.concatenate([np.asarray(im) for im in imgs], axis=1)
p = RP.fresh(os.path.join(OUT, "EYE_DROP.png"))
Image.fromarray(sheet).save(p)
print("-> %s (%dx%d)" % (p, sheet.shape[1], sheet.shape[0]))

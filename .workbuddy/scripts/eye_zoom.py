# -*- coding: utf-8 -*-
"""眼部特写：用可信的取景（probe_eye_isolate 同款）渲染整幅，再按解析计算出的
像素坐标裁出眼部区域放大，避免"取景错位看不出东西"。

只读。输出 PNG 到 vysna_out3/_eyetest/。
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
      r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out3")
MESH = os.path.join(V3, "Vysna_infantry.mesh")
OUT = os.path.join(V3, "_eyetest")

EXCLUDE_KEYS = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
                "裙+", "颜3", "颜4"]
MAT_GROUP = {
    "颜": "face", "颜2": "face", "颜3": "face", "颜4": "face", "睫": "face",
    "眉": "face", "白目": "face", "目": "face", "瞳": "face", "目光": "face",
    "鼻线": "face", "口舌": "face", "齿": "face", "星目": "face", "照れ": "face",
}
EYE_MATS = ["白目", "目", "瞳", "目光", "星目"]
SKIN_MATS = ["颜", "颜2"]
LASH_MATS = ["睫", "眉"]

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
print("face 节点 #%d 三角 %d" % (face_i, out_tri))


def seg_idx(names, invert=False):
    idx = np.concatenate([np.arange(a, a + n) for nm, a, n in segs if nm in names]) \
        if names else np.array([], np.int64)
    if invert:
        return np.setdiff1d(np.arange(out_tri), idx)
    return idx


# 眼球中心（原始坐标）
eye_v = np.unique(np.concatenate(
    [FACE["T"][a:a + n].ravel() for nm, a, n in segs if nm in EYE_MATS]))
EYE_C = FACE["P"][eye_v].mean(0)
print("眼球中心 = (%.4f, %.4f, %.4f)" % tuple(EYE_C))

# ---------- 取景（与 probe_eye_isolate 一致，可信）
W, H, ZOOM, FY = 1400, 1100, 7.0, 6.58
allP = np.concatenate([n["P"] for n in nodes], 0)
C = np.array([allP[:, 0].mean(), FY, allP[:, 2].mean()])
RAD = np.linalg.norm(allP - C, axis=1).max()
SCALE = min(W, H) / (2.0 * RAD * 1.05) * ZOOM
print("c=(%.3f,%.3f,%.3f) r=%.3f scale=%.1f px/unit" % (C[0], C[1], C[2], RAD, SCALE))

import math                                          # noqa: E402
az, el = RP.VIEWS["front"]
fwd = np.array([math.cos(az) * math.cos(el), math.sin(el), math.sin(az) * math.cos(el)])
fwd /= np.linalg.norm(fwd)
right = np.cross(fwd, np.array([0.0, 1.0, 0.0]))
right /= np.linalg.norm(right)
up = np.cross(right, fwd)
rel = EYE_C - C
PX = W / 2 + (rel @ right) * SCALE
PY = H / 2 - (rel @ up) * SCALE
print("眼球在图上的像素位置 = (%.0f, %.0f)" % (PX, PY))

# 裁一个覆盖双眼的框（眼心 y 上下 ±0.16 单位，x 左右 ±0.30 单位）
hw = int(0.30 * SCALE)
hh = int(0.16 * SCALE)
BOX = (int(PX - hw), int(PY - hh), int(PX + hw), int(PY + hh))
print("裁剪框 = %s  (w=%d h=%d)" % (BOX, BOX[2] - BOX[0], BOX[3] - BOX[1]))


def crop_label(img, text):
    im = Image.fromarray(img).crop(BOX)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 260, 18], fill=(0, 0, 0))
    d.text((4, 4), text, fill=(255, 235, 120))
    return im


def only(tri_idx):
    out = []
    for i, n in enumerate(nodes):
        if i != face_i:
            out.append(n)
            continue
        d = dict(n)
        d["T"] = n["T"][tri_idx]
        out.append(d)
    return out


# ==================== 面板 A：分层拆解，确认脸皮是否盖住眼睛 ====================
panels = [
    ("1 eyes only (白目/目/瞳/目光/星目)", only(seg_idx(EYE_MATS))),
    ("2 skin only (颜/颜2)", only(seg_idx(SKIN_MATS))),
    ("3 skin+lash (颜/颜2/睫/眉)", only(seg_idx(SKIN_MATS + LASH_MATS))),
    ("4 all face", only(np.arange(out_tri))),
]
imgs = []
for cap, ns in panels:
    a = RP.render(ns, V3, W, H, RP.VIEWS["front"], zoom=ZOOM, focus_y=FY, cull=False)
    imgs.append(crop_label(a, cap))
    print("  面板 %s" % cap)
sheet = np.concatenate([np.asarray(im) for im in imgs], axis=1)
p = RP.fresh(os.path.join(OUT, "EYE_LAYERS.png"))
Image.fromarray(sheet).save(p)
print("-> %s (%dx%d)" % (p, sheet.shape[1], sheet.shape[0]))

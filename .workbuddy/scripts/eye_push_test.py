# -*- coding: utf-8 -*-
"""眼球前推量扫描：把眼球各层整体沿 -Z 平移若干量，渲染头部特写拼图，目视定档。

只读（输出 PNG 到 vysna_out3 所在的 _eyetest 目录，会自动避让命名）。
"""
import os
import sys

import numpy as np
from PIL import Image

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
fi = None
for i, nd in enumerate(nodes):
    if len(nd["T"]) == out_tri:
        fi = i
print("face 节点 = #%d，三角 %d" % (fi, out_tri))

eye_tris = np.concatenate([np.arange(a, a + n) for nm, a, n in segs
                           if nm in EYE_MATS])
for nm, a, n in segs:
    if nm in EYE_MATS:
        print("   %-4s 三角 %d" % (nm, n))
print("眼球三角合计 %d" % len(eye_tris))


def shifted(delta):
    """返回一份 nodes 副本：眼球三角改用独立顶点并沿 -Z 平移 delta。
    同时把整份网格平移，使「眼球中心」落在 render() 的相机中心上
    （render 只接受 focus_y，x/z 取全体顶点均值，所以必须先把均值挪到眼球中心）。"""
    nd = dict(nodes[fi])
    P, T = nd["P"], nd["T"].copy()
    mp = {}
    newP = []
    for t in eye_tris:
        for s in range(3):
            v = int(T[t, s])
            k = mp.get(v)
            if k is None:
                k = len(P) + len(newP)
                mp[v] = k
                newP.append(P[v] + np.array([0.0, 0.0, -delta]))
            T[t, s] = k
    nd["P"] = np.concatenate([P, np.array(newP).reshape(-1, 3)], 0)
    nd["UV"] = np.concatenate([nodes[fi]["UV"],
                               nodes[fi]["UV"][list(mp.keys())]], 0)
    nd["N"] = np.concatenate([nodes[fi]["N"],
                              nodes[fi]["N"][list(mp.keys())]], 0)
    out = list(nodes)
    out[fi] = nd
    return out


def recenter(nds):
    """平移所有节点，使全体顶点均值 = 眼球中心（这样 focus_y 就是眼心 y）。"""
    allP = np.concatenate([n["P"] for n in nds], 0)
    D = allP.mean(0) - EYE_C
    out = []
    for n in nds:
        m = dict(n)
        m["P"] = n["P"] - D
        out.append(m)
    return out, float(EYE_C[1])


# 眼球中心（用白目/目/瞳/目光的顶点均值）
eye_v = np.unique(np.concatenate(
    [nodes[fi]["T"][a:a + n].ravel() for nm, a, n in segs if nm in EYE_MATS]))
EYE_C = nodes[fi]["P"][eye_v].mean(0)
print("眼球中心 = (%.4f, %.4f, %.4f)  眼球半径 y 跨度 %.4f"
      % (EYE_C[0], EYE_C[1], EYE_C[2],
         np.ptp(nodes[fi]["P"][eye_v][:, 1])))

DELTAS = [0.000, 0.010, 0.020, 0.030, 0.045, 0.060]
W, H = 420, 420
os.makedirs(OUT, exist_ok=True)

rows = []
for le in (False, True):
    tiles = []
    for d in DELTAS:
        nds, fy = recenter(shifted(d))
        img = RP.render(nds, V3, W, H, RP.VIEWS["front"],
                        zoom=20.0, focus_y=fy, depth_le=le, cull=True)
        tiles.append(img)
        print("  渲染 delta=%.3f depth_le=%s" % (d, le))
    rows.append(np.concatenate(tiles, axis=1))

sheet = np.concatenate(rows, axis=0)
p = RP.fresh(os.path.join(OUT, "EYE_SWEEP_push.png"))
Image.fromarray(sheet).save(p)
print("-> %s  (%dx%d)" % (p, sheet.shape[1], sheet.shape[0]))
print("   上排 depth '<'（LESS），下排 depth '<='（LESS_EQUAL）")
print("   列依次 delta = %s" % DELTAS)

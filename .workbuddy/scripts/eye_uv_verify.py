# -*- coding: utf-8 -*-
"""核对 v6 里 目 材质的 UV 是否落在正确的图集 cell 内，并直接采样看颜色。"""
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402
from pdx_data import read_meshfile             # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
V6 = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
      r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out6")

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
UV = np.array(pmx.v_uv, np.float64)
faces = np.array(pmx.faces, np.int64)

EXCLUDE = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
           "裙+", "颜3", "颜4"]
FG = {"颜", "颜2", "睫", "眉", "白目", "目", "瞳", "目光", "鼻线", "口舌",
      "齿", "星目", "照れ"}
segs = {}
acc = 0
for mt in pmx.materials:
    nm = mt["name"]
    cnt = mt["face_count"] // 3
    if not any(k in nm for k in EXCLUDE) and nm in FG:
        segs[nm] = (acc, cnt, mt["tex"])
        acc += cnt

# ---- 从 build_report 里读图集布局
rep = open(os.path.join(V6, "build_report.txt"), encoding="utf-8").read()
print("build_report 图集行：")
for ln in rep.splitlines():
    if "图集" in ln and ("face" in ln or "贴图" in ln):
        print("   " + ln.strip())

# ---- 从写好的 mesh 里读 face 节点的 u0
root = read_meshfile(os.path.join(V6, "Vysna_infantry.mesh"))
FACE = None
for o in root:
    for sh in o:
        for m in sh.findall("mesh"):
            if "p" not in m.attrib:
                continue
            tri = np.array(m.get("tri"), np.int64)
            if len(tri) // 3 == acc:
                FACE = m
print("\nface 节点三角 = %d" % (len(FACE.get("tri")) // 3))
U0 = np.array(FACE.get("u0"), np.float64).reshape(-1, 2)
print("图集 UV 范围: u [%.4f, %.4f]  v [%.4f, %.4f]"
      % (U0[:, 0].min(), U0[:, 0].max(), U0[:, 1].min(), U0[:, 1].max()))

# ---- 图集实际大小
AT = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
      r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out6\vysna_face_atlas.png")
im = Image.open(AT).convert("RGBA")
a = np.asarray(im, np.uint8)
AH, AW = a.shape[0], a.shape[1]
print("图集 %dx%d" % (AW, AH))


def sample(uv):
    x = int(np.clip(uv[0] * AW, 0, AW - 1))
    y = int(np.clip(uv[1] * AH, 0, AH - 1))
    return a[y, x]


# ---- 逐材质：把「重映射后的 uv」和「重映射前应落在贴图中的位置」对照
print("\n各眼球材质在图集里的采样")
print("-" * 78)
for nm in ["白目", "目", "瞳", "目光", "星目"]:
    if nm not in segs:
        continue
    A, N, ti = segs[nm]
    # face 节点里的三角顺序 = 保留材质的顺序；算出该材质在 face 里的偏移
    off = 0
    for k, mt in enumerate(pmx.materials):
        knm = mt["name"]
        cnt = mt["face_count"]
        if any(kk in knm for kk in EXCLUDE) or knm not in FG:
            continue
        if knm == nm:
            break
        off += cnt
    start = off
    T = np.array(FACE.get("tri"), np.int64)[start:start + N * 3]
    U = U0[T]
    cols = np.array([sample(u) for u in U[::7]])
    print("  %-4s 三角 %4d  图集uv u[%.4f,%.4f] v[%.4f,%.4f]  采样RGB均值 %s"
          % (nm, N, U[:, 0].min(), U[:, 0].max(), U[:, 1].min(), U[:, 1].max(),
             tuple(int(x) for x in cols[:, :3].mean(0))))

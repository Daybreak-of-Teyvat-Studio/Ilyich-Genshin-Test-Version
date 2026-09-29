# -*- coding: utf-8 -*-
"""从写好的 .mesh 里按 face 组的材质偏移，精确切出每个材质的 uv，
算出它们在【图集空间】的真实范围，并统计采样颜色。

关键：face 节点 tri 的排列 = 保留材质按 PMX 顺序；但顶点去重后
顶点号会重排，所以必须用 tri 分段，不能假设 uv 数组顺序 = 材质顺序。
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402
from pdx_data import read_meshfile             # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
OUT = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out6")

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
EXCLUDE = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
           "裙+", "颜3", "颜4"]
FG = {"颜", "颜2", "睫", "眉", "白目", "目", "瞳", "目光", "鼻线", "口舌",
      "齿", "星目", "照れ"}

# face 组材质顺序 + 三角数
seq = []
for mt in pmx.materials:
    nm = mt["name"]
    if any(k in nm for k in EXCLUDE) or nm not in FG:
        continue
    seq.append((nm, mt["face_count"] // 3))

root = read_meshfile(os.path.join(OUT, "Vysna_infantry.mesh"))
FACE = None
tot = sum(n for _, n in seq)
for o in root:
    for sh in o:
        for m in sh.findall("mesh"):
            if "p" in m.attrib and len(np.array(m.get("tri"))) // 3 == tot:
                FACE = m
T = np.array(FACE.get("tri"), np.int64).reshape(-1, 3)
U0 = np.array(FACE.get("u0"), np.float64).reshape(-1, 2)

a = np.asarray(Image.open(os.path.join(OUT, "vysna_face_atlas.png")).convert("RGBA"),
               np.uint8)
AH, AW = a.shape[0], a.shape[1]


def samp(uv):
    x = int(np.clip(uv[0] * AW, 0, AW - 1))
    y = int(np.clip(uv[1] * AH, 0, AH - 1))
    return a[y, x]


out = []
out.append("从 .mesh 精确切出的各材质图集 UV 范围（图集 %dx%d）" % (AW, AH))
out.append("=" * 92)
out.append("%-5s %6s %9s %9s %9s %9s %9s %s"
           % ("材质", "三角", "u_min", "u_max", "v_min", "v_max", "越界", "采样RGB均值"))
cur = 0
for nm, n in seq:
    idx = T[cur:cur + n].ravel()
    U = U0[idx]
    oob = ((U[:, 0] < 0) | (U[:, 0] > 1) | (U[:, 1] < 0) | (U[:, 1] > 1)).sum()
    cols = np.array([samp(u) for u in U[::max(1, len(U) // 300)]])
    out.append("%-5s %6d %9.4f %9.4f %9.4f %9.4f %9d %s"
               % (nm, n, U[:, 0].min(), U[:, 0].max(),
                  U[:, 1].min(), U[:, 1].max(), oob,
                  tuple(int(x) for x in cols[:, :3].mean(0))))
    cur += n

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_eye_final.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_eye_final_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % p)

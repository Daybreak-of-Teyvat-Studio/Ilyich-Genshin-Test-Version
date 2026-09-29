# -*- coding: utf-8 -*-
"""检查各材质在源贴图上采样到的 alpha —— 我的软件预览器忽略 alpha，
HOI4 不忽略。若某材质采样出来大部分 alpha=0，游戏里就是「看不见」。
重点看翅膀材质 翼 / 翼2（它们用 髮.png）。
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmx_parse import PMX  # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "report_alpha_check.txt")

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))

L = []
P = L.append

tex_cache = {}


def tex(ti):
    if ti not in tex_cache:
        p = pmx.textures[ti].replace("\\", os.sep).replace("/", os.sep)
        im = Image.open(os.path.join(SRC, p)).convert("RGBA")
        tex_cache[ti] = np.asarray(im, np.uint8)
    return tex_cache[ti]


P("%-14s %5s %6s %-28s %-24s %s"
  % ("材质", "三角", "贴图", "贴图路径", "UV 包围盒(u0,u1,v0,v1)", "采样 alpha: 全透明% 半透明% 不透明%  RGB 均值"))
P("-" * 130)

acc = 0
for mt in pmx.materials:
    nm = mt["name"]
    ti = mt["tex"]
    n_tri = mt["face_count"] // 3
    st = acc
    acc += mt["face_count"]
    if not (0 <= ti < len(pmx.textures)):
        P("%-14s %5d %6s %-28s" % (nm, n_tri, ti, "(无贴图)"))
        continue
    a = tex(ti)
    H, W = a.shape[:2]
    # 采样该材质所有顶点
    vidx = []
    for k in range(st, st + mt["face_count"], 3):
        vidx.extend((pmx.faces[k], pmx.faces[k + 1], pmx.faces[k + 2]))
    vidx = np.array(sorted(set(vidx)), np.int64)
    uv = np.array(pmx.v_uv)[vidx]
    u = np.mod(uv[:, 0], 1.0)
    v = np.mod(uv[:, 1], 1.0)
    x = np.clip((u * W).astype(np.int64), 0, W - 1)
    y = np.clip((v * H).astype(np.int64), 0, H - 1)
    s = a[y, x]
    al = s[:, 3].astype(np.float64)
    zero = float((al < 8).mean() * 100)
    mid = float(((al >= 8) & (al < 248)).mean() * 100)
    op = float((al >= 248).mean() * 100)
    rgb = s[:, :3].mean(0)
    P("%-14s %5d %6d %-28s (%5.3f,%5.3f,%5.3f,%5.3f)  %6.1f %6.1f %6.1f   (%3.0f,%3.0f,%3.0f)"
      % (nm, n_tri, ti, pmx.textures[ti].replace("\\", "/")[-26:],
         u.min(), u.max(), v.min(), v.max(), zero, mid, op, rgb[0], rgb[1], rgb[2]))

txt = "\n".join(L)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
print("\n-> " + OUT)

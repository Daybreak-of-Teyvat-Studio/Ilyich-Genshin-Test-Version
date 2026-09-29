# -*- coding: utf-8 -*-
"""眼球三角 UV 覆盖热力图：把 目/白目 材质的每个三角在其贴图空间里画出来，
看它们到底覆盖了贴图的哪一块。用于判断"压扁贴片"的真实取值区域。"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
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
        segs[nm] = (acc, cnt, mt["tex"], mt["draw_flag"])
        acc += cnt

out = []


def report(nm):
    a, n, ti, fl = segs[nm]
    T = faces[3 * a:3 * (a + n)].reshape(-1, 3)
    f = T.ravel()
    u, v = UV[f, 0], UV[f, 1]
    out.append("%-5s 三角 %4d  顶点 %4d  贴图 %s  flag=0x%02x"
               % (nm, n, len(np.unique(f)), pmx.textures[ti], fl))
    out.append("      u [%8.4f, %8.4f]   v [%8.4f, %8.4f]"
               % (u.min(), u.max(), v.min(), v.max()))
    # 负 v 占比
    out.append("      v<0 的顶点 %d / %d (%.1f%%)   v<-0.5 的 %d"
               % ((v < 0).sum(), len(v), (v < 0).mean() * 100, (v < -0.5).sum()))
    # v+1 后的范围
    v2 = np.mod(v + 1.0, 1.0)
    out.append("      用 v+1 再取模后： v [%8.4f, %8.4f]   v<0.02 的 %d (%.1f%%)"
               % (v2.min(), v2.max(), (v2 < 0.02).sum(), (v2 < 0.02).mean() * 100))
    return T


out.append("眼球材质 UV 平面诊断")
out.append("=" * 84)
Ts = {}
for nm in ["白目", "目", "瞳", "目光", "星目"]:
    Ts[nm] = report(nm)
    out.append("")

# 画 uv 图：0..1 与 -1..1 两张
for tag, (lo, hi) in [("01", (0.0, 1.0)), ("n1", (-1.0, 1.0))]:
    S = 800
    img = Image.new("RGB", (S, S), (14, 14, 18))
    d = ImageDraw.Draw(img)

    def px(u, v):
        uu = (u - lo) / (hi - lo)
        vv = (v - lo) / (hi - lo)
        return (uu * (S - 1), (1.0 - vv) * (S - 1))

    # 网格
    for k in np.arange(np.ceil(lo * 4) / 4, hi + 1e-9, 0.25):
        x, _ = px(k, lo)
        _, y = px(lo, k)
        g = 70 if abs(k - round(k)) < 1e-6 else 34
        d.line([(x, 0), (x, S)], fill=(g, g, g))
        d.line([(0, y), (S, y)], fill=(g, g, g))
    COL = {"白目": (255, 110, 110), "目": (110, 230, 110), "瞳": (110, 160, 255),
           "目光": (255, 240, 110), "星目": (230, 120, 255)}
    for nm, T in Ts.items():
        for t in T:
            d.polygon([px(UV[i, 0], UV[i, 1]) for i in t], outline=COL[nm])
    d.text((6, 6), "uv range [%.0f, %.0f]  red=白目 green=目 blue=瞳" % (lo, hi),
           fill=(240, 240, 240))
    p = os.path.join(HERE, "report_eye_uvmap_%s.png" % tag)
    i = 2
    while os.path.exists(p):
        p = os.path.join(HERE, "report_eye_uvmap_%s_%d.png" % (tag, i))
        i += 1
    img.save(p)
    out.append("UV 图 %s -> %s" % (tag, p))

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_eye_plane.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_eye_plane_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % p)

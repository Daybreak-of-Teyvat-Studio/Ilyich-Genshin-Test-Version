# -*- coding: utf-8 -*-
"""批量：把各模型眼部材质的 UV 采样点画回它的源贴图，一眼判断
「目」是不是一张完整的眼睛、需不需要前推、哪些叠层该剔。"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pmx_parse import PMX  # noqa: E402

WORK = r"C:\Users\XIANGZIYUAN\vysna_work"
MODELS = [("心海", "珊瑚宫心海.pmx", "Kokomi"),
          ("妮露", "妮露.pmx", "Nilou"),
          ("少女", "少女.pmx", "Columbina"),
          ("茜特菈莉", "茜特拉莉.pmx", "Citlali")]
EYE_KEYS = ("目", "白目", "星目", "瞳", "目光", "眼罩")

CW = 300
rows = []
L = []

for dirname, pmxfile, tag in MODELS:
    src = os.path.join(WORK, dirname)
    p = PMX(os.path.join(src, pmxfile))
    VP = np.asarray(p.v_pos, np.float64)
    VUV = np.asarray(p.v_uv, np.float64)
    mats = []
    acc = 0
    for mt in p.materials:
        nm = mt["name"]
        st, cnt = acc, mt["face_count"]
        acc += cnt
        if any(k in nm for k in EYE_KEYS):
            mats.append((nm, mt["tex"], st, cnt))
    L.append("\n=== %s (%s) 眼部材质 %d 个" % (tag, dirname, len(mats)))
    for nm, ti, st, cnt in mats:
        n_tri = cnt // 3
        # 该材质的三角形质心位置（看它是不是一对眼）
        cen = []
        pts = []
        for k in range(st, st + cnt, 3):
            f0, f1, f2 = p.faces[k], p.faces[k + 1], p.faces[k + 2]
            cen.append((VP[f0] + VP[f1] + VP[f2]) / 3.0)
            for f in (f0, f1, f2):
                u, v = VUV[f]
                pts.append((u - np.floor(u), v - np.floor(v)))
        cen = np.asarray(cen)
        pts = np.asarray(pts)
        if not (0 <= ti < len(p.textures)):
            L.append("   %-8s %5d tri  无贴图  世界 y[%.2f,%.2f] x[%.2f,%.2f]"
                     % (nm, n_tri, cen[:, 1].min(), cen[:, 1].max(),
                        cen[:, 0].min(), cen[:, 0].max()))
            continue
        texp = p.textures[ti].replace("\\", os.sep).replace("/", os.sep)
        im = Image.open(os.path.join(src, texp)).convert("RGBA")
        W, H = im.size
        a = np.asarray(im, np.uint8).copy()
        x = np.clip((pts[:, 0] * W).astype(np.int64), 0, W - 1)
        # ★ MMD/OpenGL 约定 v=0 在贴图底部，PIL 行 0 在顶部 -> 必须镜像
        y = np.clip(((1.0 - pts[:, 1]) * H).astype(np.int64), 0, H - 1)
        # 采样点的 alpha 统计
        al = a[y, x, 3].astype(np.float64)
        a[y, x] = [255, 0, 0, 255]
        up = Image.fromarray(a).resize((CW, CW), Image.NEAREST)
        ImageDraw.Draw(up).text((5, 5), "%d %s" % (len(rows) + 1, nm),
                                fill=(255, 255, 0))
        rows.append(up)
        L.append("   %-8s %5d tri  tex=%-14s 世界 y[%.2f,%.2f] x[%.2f,%.2f]  "
                 "采样 alpha 中位 %.0f 全透明%.0f%%  UV u[%.2f,%.2f] v[%.2f,%.2f]"
                 % (nm, n_tri, os.path.basename(texp),
                    cen[:, 1].min(), cen[:, 1].max(),
                    cen[:, 0].min(), cen[:, 0].max(),
                    np.median(al), (al < 8).mean() * 100,
                    pts[:, 0].min(), pts[:, 0].max(),
                    pts[:, 1].min(), pts[:, 1].max()))

ncol = 5
nrow = (len(rows) + ncol - 1) // ncol
sheet = Image.new("RGB", (ncol * CW, nrow * CW), (30, 30, 30))
for i, im in enumerate(rows):
    sheet.paste(im.convert("RGB"), ((i % ncol) * CW, (i // ncol) * CW))
outp = os.path.join(HERE, "report_eye_probe_sheet.png")
sheet.save(outp)
txt = "\n".join(L)
open(os.path.join(HERE, "report_eye_probe.txt"), "w", encoding="utf-8").write(txt)
print(txt)
print("\n-> %s" % outp)

# -*- coding: utf-8 -*-
"""批量：把各模型眼部材质的「UV 区域对应贴图块」裁出来放大，一眼判断
该材质到底是不是一只眼睛、要不要前推、哪些叠层该剔。

★ v 轴：MMD/OpenGL 约定 v=0 在贴图底部，PIL 行 0 在顶部 -> y = (1-v)*H
"""
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
EYE_KEYS = ("目", "白目", "星目", "瞳", "目光", "眼罩", "二重")
CW = 300

rows, L = [], []

for dirname, pmxfile, tag in MODELS:
    src = os.path.join(WORK, dirname)
    p = PMX(os.path.join(src, pmxfile))
    VP = np.asarray(p.v_pos, np.float64)
    VUV = np.asarray(p.v_uv, np.float64)
    mats = []
    acc = 0
    for mt in p.materials:
        nm, st, cnt = mt["name"], acc, mt["face_count"]
        acc += cnt
        if any(k in nm for k in EYE_KEYS):
            mats.append((nm, mt["tex"], st, cnt))
    L.append("\n=== %s (%s) 眼部材质 %d 个" % (tag, dirname, len(mats)))
    for nm, ti, st, cnt in mats:
        n_tri = cnt // 3
        cen, pts = [], []
        for k in range(st, st + cnt, 3):
            f0, f1, f2 = p.faces[k], p.faces[k + 1], p.faces[k + 2]
            cen.append((VP[f0] + VP[f1] + VP[f2]) / 3.0)
            for f in (f0, f1, f2):
                u, v = VUV[f]
                pts.append((u - np.floor(u), v - np.floor(v)))
        cen = np.asarray(cen)
        c0, c1 = cen[:, 1].min(), cen[:, 1].max()
        x0, x1 = cen[:, 0].min(), cen[:, 0].max()
        if not (0 <= ti < len(p.textures)):
            L.append("   %-8s %5d tri  无贴图  y[%.2f,%.2f] x[%.2f,%.2f]"
                     % (nm, n_tri, c0, c1, x0, x1))
            continue
        texp = p.textures[ti].replace("\\", os.sep).replace("/", os.sep)
        im = Image.open(os.path.join(src, texp)).convert("RGBA")
        W, H = im.size
        pts = np.asarray(pts)
        u0, u1 = pts[:, 0].min(), pts[:, 0].max()
        v0, v1 = pts[:, 1].min(), pts[:, 1].max()
        px0, px1 = int(u0 * W), min(W, int(u1 * W) + 1)
        py0, py1 = int((1.0 - v1) * H), min(H, int((1.0 - v0) * H) + 1)
        if px1 - px0 < 2 or py1 - py0 < 2:
            px0, px1, py0, py1 = 0, W, 0, H
        crop = im.crop((px0, py0, px1, py1)).resize((CW, CW), Image.NEAREST)
        arr = np.asarray(crop.convert("RGBA"))
        al = arr[:, :, 3].astype(np.float64)
        ctr = arr[arr.shape[0] // 2, arr.shape[1] // 2]
        lab = "%d %s.%s" % (len(rows) + 1, tag[:4], nm)
        ImageDraw.Draw(crop).text((4, 4), lab, fill=(255, 255, 0))
        rows.append(crop.convert("RGB"))
        L.append("   %-8s %5d tri  tex=%-12s y[%.2f,%.2f] x[%.2f,%.2f]  "
                 "UV u[%.2f,%.2f] v[%.2f,%.2f]  中心 a=%d rgb=(%d,%d,%d)  区域内全透明%.0f%%"
                 % (nm, n_tri, os.path.basename(texp), c0, c1, x0, x1,
                    u0, u1, v0, v1, ctr[3], ctr[0], ctr[1], ctr[2],
                    (al < 8).mean() * 100))

ncol = 5
nrow = (len(rows) + ncol - 1) // ncol
sheet = Image.new("RGB", (ncol * CW, nrow * CW), (25, 25, 25))
for i, im in enumerate(rows):
    sheet.paste(im, ((i % ncol) * CW, (i // ncol) * CW))
outp = os.path.join(HERE, "report_eye_probe_sheet.png")
sheet.save(outp)
txt = "\n".join(L)
open(os.path.join(HERE, "report_eye_probe.txt"), "w", encoding="utf-8").write(txt)
print(txt)
print("\n-> %s" % outp)

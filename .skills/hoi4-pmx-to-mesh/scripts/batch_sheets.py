# -*- coding: utf-8 -*-
"""批量渲染验证：每个模型出「带贴图四视图」+「走路 f0/f12 正面/侧面」，拼成一张图。"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
OUT_ROOT = os.path.join(HERE, "..", "models_out")
ANIM = (r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
        r"\gfx\models\units\GER_infantry_moving_rifle.anim")
NAMES = ["Kokomi", "Nilou", "Columbina", "Citlali"]
POSED = os.path.join(HERE, "_posetest")

PLAN = [                       # (脚本, 参数, 产物文件, 标签)
    ("render_preview.py", ["--views", "front,back,left,q34", "--w", "330", "--h", "540"],
     ["preview_T_front.png", "preview_T_back.png", "preview_T_left.png",
      "preview_T_q34.png"], "T"),
    ("pose_render.py", ["--frame", "12", "--views", "front,left", "--w", "330", "--h", "540"],
     ["{tag}_f12_front.png", "{tag}_f12_left.png"], "P"),
]

rows = []
for nm in NAMES:
    mesh = os.path.join(OUT_ROOT, nm, "%s_infantry.mesh" % nm)
    if not os.path.isfile(mesh):
        print("!! 缺 %s" % mesh)
        continue
    row = []
    # 带贴图四视图
    subprocess.run([PY, os.path.join(HERE, "render_preview.py"), mesh,
                    "--tag", "T_", "--views", "front,back,left,q34",
                    "--w", "330", "--h", "540"],
                   cwd=os.path.join(OUT_ROOT, nm), capture_output=True)
    for f in ("preview_T_front.png", "preview_T_back.png",
              "preview_T_left.png", "preview_T_q34.png"):
        p = os.path.join(OUT_ROOT, nm, f)
        row.append((Image.open(p).convert("RGB"), f) if os.path.isfile(p) else None)
    # 走路
    for fr in (0, 12):
        tag = "B_%s_f%d" % (nm, fr)
        subprocess.run([PY, os.path.join(HERE, "pose_render.py"), mesh, ANIM,
                        "--frame", str(fr), "--outdir", "_posetest", "--tag", tag,
                        "--views", "front,left", "--w", "330", "--h", "540"],
                       cwd=HERE, capture_output=True)
        for v in ("front", "left"):
            p = os.path.join(POSED, "%s_%s.png" % (tag, v))
            row.append((Image.open(p).convert("RGB"), "%s f%d %s" % (nm, fr, v))
                       if os.path.isfile(p) else None)
    rows.append((nm, row))

CW, CH, HDR = 330, 540, 26
ncol = max(len(r[1]) for r in rows) if rows else 1
sheet = Image.new("RGB", (CW * ncol, (CH + HDR) * len(rows)), (22, 22, 22))
d = ImageDraw.Draw(sheet)
for i, (nm, row) in enumerate(rows):
    y = i * (CH + HDR)
    d.text((6, y + 8), nm, fill=(255, 255, 0))
    for j, item in enumerate(row):
        if item is None:
            continue
        im, lab = item
        sheet.paste(im, (j * CW, y + HDR))
        d.text((j * CW + 4, y + 10), lab.replace(nm, "").strip()[:28],
               fill=(120, 255, 120))
outp = os.path.join(HERE, "_posetest", "DELIVER_batch_all.png")
sheet.save(outp)
print("->", outp, sheet.size)

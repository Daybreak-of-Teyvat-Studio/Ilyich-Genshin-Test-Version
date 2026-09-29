# -*- coding: utf-8 -*-
"""把最终部署版的渲染拼成一张交付预览图。"""
import os
import numpy as np
from PIL import Image, ImageDraw

D = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
     r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
     r"\gfx\models\units\DOT_Vysna")
OUT = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_final\薇斯纳_模型预览.png")

body = Image.open(os.path.join(D, "preview_dep_body_sheet.png")).convert("RGB")
head = Image.open(os.path.join(D, "preview_dep_head_front.png")).convert("RGB")

ROWH = 560
bw = int(body.size[0] * ROWH / body.size[1])
body = body.resize((bw, ROWH), Image.LANCZOS)
head = head.resize((ROWH, ROWH), Image.LANCZOS)

PAD = 18
W = PAD + ROWH + PAD + bw + PAD
canvas = Image.new("RGB", (W, ROWH + 40 + 2 * PAD), (18, 20, 26))
canvas.paste(head, (PAD, 40 + PAD))
canvas.paste(body, (PAD + ROWH + PAD, 40 + PAD))

d = ImageDraw.Draw(canvas)
d.text((PAD, 12), "薇斯纳 Vysna  |  HOI4 步兵单位模型  |  45,535 顶点 / 53,300 三角 / 3 draw call", fill=(225, 235, 245))
d.text((PAD, 28), "33 根标准骨骼（直接复用原版步兵动画）  |  scale 0.85  |  贴图 1024x2048 + 1024x1024 DXT5", fill=(150, 165, 180))
canvas.save(OUT)
print("->", OUT, canvas.size)

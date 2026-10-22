# -*- coding: utf-8 -*-
"""把眼睛相关的源贴图放大并排，用于肉眼确认「睁眼 / 闭眼」的内容分别在哪张图上。"""
import os
from PIL import Image

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳\tex"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "report_eye_tex_big.png")

names = ["目.png", "目2.png", "瞳.png", "目光.png"]
S = 380
tiles = []
for n in names:
    p = os.path.join(SRC, n)
    im = Image.open(p).convert("RGBA")
    im.thumbnail((S, S), Image.LANCZOS)
    canvas = Image.new("RGB", (S, S), (255, 255, 255))
    canvas.paste(im, ((S - im.width) // 2, (S - im.height) // 2), im)
    tiles.append(canvas)

sheet = Image.new("RGB", (S * len(tiles), S), (255, 255, 255))
for i, t in enumerate(tiles):
    sheet.paste(t, (i * S, 0))
sheet.save(OUT)
print(OUT, sheet.size, "| 顺序:", ", ".join(names))

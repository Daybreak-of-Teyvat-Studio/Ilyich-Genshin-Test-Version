# -*- coding: utf-8 -*-
"""把眼部相关贴图并排渲染出来（含 alpha 合成棋盘格），用于人工判读。"""
import os
import numpy as np
from PIL import Image, ImageDraw

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳\tex"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\scripts\report_eye_textures.png"

NAMES = ["目.png", "目2.png", "瞳.png", "目光.png", "颜.png", "表情.png"]

CELL = 320
cols = len(NAMES)
canvas = Image.new("RGBA", (CELL * cols, CELL + 22), (255, 255, 255, 255))
d = ImageDraw.Draw(canvas)

for i, nm in enumerate(NAMES):
    p = os.path.join(SRC, nm)
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    s = min(CELL / w, CELL / h)
    im2 = im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.NEAREST)
    # 棋盘格底，便于看 alpha
    bg = Image.new("RGBA", (CELL, CELL), (200, 200, 200, 255))
    for yy in range(0, CELL, 16):
        for xx in range(0, CELL, 16):
            if ((xx // 16) + (yy // 16)) % 2 == 0:
                bg.paste((160, 160, 160, 255), (xx, yy, xx + 16, yy + 16))
    ox = (CELL - im2.size[0]) // 2
    oy = (CELL - im2.size[1]) // 2
    bg.alpha_composite(im2, (ox, oy))
    canvas.paste(bg, (i * CELL, 22))

    a = np.array(im)
    vis = (a[..., 3] > 8).mean() if a.shape[-1] == 4 else 1.0
    rgb = a[..., :3][a[..., 3] > 8] if a.shape[-1] == 4 else a[..., :3].reshape(-1, 3)
    mean_rgb = rgb.mean(0) if len(rgb) else (0, 0, 0)
    d.text((i * CELL + 4, 5),
           "%s  %dx%d  可见%.1f%%  RGB(%.0f,%.0f,%.0f)"
           % (nm, w, h, vis * 100, mean_rgb[0], mean_rgb[1], mean_rgb[2]),
           fill=(0, 0, 0))

canvas.convert("RGB").save(OUT)
print("写出", OUT)

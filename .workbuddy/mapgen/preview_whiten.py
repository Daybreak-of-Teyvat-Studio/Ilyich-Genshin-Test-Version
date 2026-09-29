# -*- coding: utf-8 -*-
"""生成不同高度阈值下的 terrain 白化预览（缩略拼图）"""
import os, io
import numpy as np
from PIL import Image, ImageDraw

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
H = os.path.join(G, ".workbuddy")

hm = np.array(Image.open(os.path.join(G, "map", "heightmap.bmp")))
tb = np.array(Image.open(os.path.join(G, "map", "terrain.bmp"))).copy()
land = hm >= 94

THS = [150, 160, 165, 170, 175]
imgs = []
for th in THS:
    a = tb.copy()
    m = land & (hm >= th)
    a[m] = (255, 255, 255)
    im = Image.fromarray(a).resize((1024, 512), Image.NEAREST)
    d = ImageDraw.Draw(im)
    txt = ">=%d  (%d px, %.2f%% land)" % (th, int(m.sum()), 100.0 * m.sum() / land.sum())
    d.rectangle([4, 4, 330, 26], fill=(0, 0, 0))
    d.text((10, 8), txt, fill=(255, 255, 255))
    imgs.append(im)

cols, rows = 2, 3
sheet = Image.new("RGB", (1024 * cols, 512 * rows), (30, 30, 30))
# 第一格放原 terrain 作对照
base = Image.fromarray(tb).resize((1024, 512), Image.NEAREST)
db = ImageDraw.Draw(base)
db.rectangle([4, 4, 200, 26], fill=(0, 0, 0))
db.text((10, 8), "ORIGINAL terrain", fill=(255, 255, 255))
sheet.paste(base, (0, 0))
for i, im in enumerate(imgs):
    k = i + 1
    sheet.paste(im, ((k % cols) * 1024, (k // cols) * 512))
out = os.path.join(H, "terrain_whiten_preview.png")
sheet.save(out)
print("WROTE", out, os.path.getsize(out))

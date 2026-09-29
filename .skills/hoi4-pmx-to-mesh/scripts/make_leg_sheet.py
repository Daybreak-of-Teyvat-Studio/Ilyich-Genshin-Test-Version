# -*- coding: utf-8 -*-
"""三版对照：未对齐 / 旧对齐(逐骨常量位移, 膝盖断裂) / 新对齐(沿腿轴连续位移)"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PT = os.path.join(HERE, "_posetest")
FIN = os.path.join(HERE, "..", "vysna_final")
V3 = os.path.join(HERE, "..", "vysna_fix3")
V4 = os.path.join(HERE, "..", "vysna_fix4")
FONT = r"C:\Windows\Fonts\msyh.ttc"


def load(p, w, h):
    im = Image.open(p).convert("RGB")
    a = np.asarray(im)
    bg = np.median(a.reshape(-1, 3), axis=0)
    mask = (np.abs(a.astype(int) - bg).sum(2) > 24).any(1)
    ys = np.where(mask)[0]
    if len(ys) > 8:
        pad = 16
        im = im.crop((0, max(0, ys[0] - pad), im.width, min(im.height, ys[-1] + pad)))
    return im.resize((w, h), Image.LANCZOS)


COLS = ["走路·正面", "走路·侧面", "腿部特写·正面", "腿部特写·侧面"]
ROWS = [
    ("① 未做对齐（网格连续，但走路两腿交叉成 X）", (255, 150, 150), [
        os.path.join(PT, "VY_BEFORE_f12_front.png"), os.path.join(PT, "VY_BEFORE_f12_left.png"),
        os.path.join(FIN, "preview_LEGf2_front.png"), os.path.join(FIN, "preview_LEGf2_left.png")]),
    ("② 旧对齐：逐骨常量位移 → 膝盖处位移台阶，大腿小腿被撕开", (255, 190, 120), [
        os.path.join(PT, "W3_f12_front.png"), os.path.join(PT, "W3_f12_left.png"),
        os.path.join(V3, "preview_LEGv3_front.png"), os.path.join(V3, "preview_LEGv3_left.png")]),
    ("③ 新对齐：沿腿轴连续位移 → 腿平滑外展，不再断裂", (150, 235, 150), [
        os.path.join(PT, "W4_f12_front.png"), os.path.join(PT, "W4_f12_left.png"),
        os.path.join(V4, "preview_LEGv4_front.png"), os.path.join(V4, "preview_LEGv4_left.png")]),
]

CW, CH = 232, 400
HDR, PAD, LBL = 40, 10, 28
W = PAD + 4 * (CW + PAD)
H = 66 + len(ROWS) * (HDR + CH + LBL + PAD) + 16
cv = Image.new("RGB", (W, H), (24, 26, 32))
d = ImageDraw.Draw(cv)
d.text((PAD + 4, 16), "薇斯纳腿部对齐方式对照（走路动画 + 腿部特写）",
       font=ImageFont.truetype(FONT, 28), fill=(255, 214, 120))

y = 66
for title, col, cells in ROWS:
    d.text((PAD + 4, y + 6), title, font=ImageFont.truetype(FONT, 21), fill=col)
    y += HDR
    for i, p in enumerate(cells):
        x = PAD + i * (CW + PAD)
        d.rectangle([x, y, x + CW, y + CH], fill=(32, 35, 42))
        if os.path.exists(p):
            cv.paste(load(p, CW, CH), (x, y))
        else:
            d.text((x + 20, y + CH // 2), "缺图\n" + os.path.basename(p),
                   font=ImageFont.truetype(FONT, 16), fill=(200, 80, 80))
        d.text((x + CW // 2 - 40, y + CH + 3), COLS[i],
               font=ImageFont.truetype(FONT, 18), fill=(215, 220, 230))
    y += CH + LBL + PAD

p = os.path.join(PT, "DELIVER_leg_fix_compare.png")
i = 2
while os.path.exists(p):
    p = os.path.join(PT, "DELIVER_leg_fix_compare_%d.png" % i)
    i += 1
cv.save(p)
print("->", p, cv.size)

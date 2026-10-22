# -*- coding: utf-8 -*-
"""拼一张「修走路 + 修翅膀」的前后对照图交付给用户。"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PT = os.path.join(HERE, "_posetest")
W3 = os.path.join(HERE, "..", "vysna_fix3")

FONT = r"C:\Windows\Fonts\msyh.ttc"
f24 = ImageFont.truetype(FONT, 26)
f26 = ImageFont.truetype(FONT, 28)
f20 = ImageFont.truetype(FONT, 21)


def load(p, w, h):
    im = Image.open(p).convert("RGB")
    # 裁掉上下多余空白：找非背景行
    a = np.asarray(im)
    bg = np.median(a.reshape(-1, 3), axis=0)
    mask = (np.abs(a.astype(int) - bg).sum(2) > 24).any(1)
    ys = np.where(mask)[0]
    if len(ys) > 8:
        pad = 26
        im = im.crop((0, max(0, ys[0] - pad), im.width, min(im.height, ys[-1] + pad)))
    return im.resize((w, h), Image.LANCZOS)


CW, CH = 300, 520
ROWS = [
    ("修复前：走路时双腿交叉成 X，翅膀不可见", [
        (os.path.join(PT, "VY_BEFORE_f12_front.png"), "正面"),
        (os.path.join(PT, "VY_BEFORE_f12_left.png"), "侧面"),
        (os.path.join(PT, "VY_BEFORE_f0_front.png"), "正面 第0帧"),
    ]),
    ("修复后：双腿正常迈步，翅膀完整保留", [
        (os.path.join(PT, "W3_f12_front.png"), "正面"),
        (os.path.join(PT, "W3_f12_left.png"), "侧面"),
        (os.path.join(PT, "W3_f0_front.png"), "正面 第0帧"),
    ]),
    ("其它动画回归：翅膀始终可见", [
        (os.path.join(PT, "W3_idle_q34.png"), "站立 idle"),
        (os.path.join(PT, "W3_atk_front.png"), "持枪攻击"),
        (os.path.join(W3, "preview_T_back.png"), "背视（带贴图）"),
    ]),
]

HDR = 46
PAD = 14
LBL = 34
W = PAD + 3 * (CW + PAD)
H = PAD + len(ROWS) * (HDR + CH + LBL + PAD) + 74
canvas = Image.new("RGB", (W, H), (24, 26, 32))
d = ImageDraw.Draw(canvas)

d.text((PAD + 4, 18), "薇斯纳模型修复对照 · HOI4 原版步兵走路动画",
       font=ImageFont.truetype(FONT, 32), fill=(255, 214, 120))

y = 74
for title, cells in ROWS:
    col = (150, 235, 150) if "修复后" in title else (
        (255, 150, 150) if "修复前" in title else (170, 205, 255))
    d.text((PAD + 4, y + 8), title, font=f26, fill=col)
    y += HDR
    for i, (p, lab) in enumerate(cells):
        x = PAD + i * (CW + PAD)
        d.rectangle([x, y, x + CW, y + CH], fill=(32, 35, 42))
        if os.path.exists(p):
            canvas.paste(load(p, CW, CH), (x, y))
        else:
            d.text((x + 20, y + CH // 2), "缺图", font=f24, fill=(200, 80, 80))
        d.text((x + CW // 2 - 34, y + CH + 5), lab, font=f20, fill=(215, 220, 230))
    y += CH + LBL + PAD

p = os.path.join(HERE, "_posetest", "DELIVER_fix_walk_wings.png")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "_posetest", "DELIVER_fix_walk_wings_%d.png" % i)
    i += 1
canvas.save(p)
print("->", p, canvas.size)

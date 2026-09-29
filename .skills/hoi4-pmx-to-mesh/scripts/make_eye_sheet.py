# -*- coding: utf-8 -*-
"""眼睛修复交付对照图：未对齐 / fix5(变闭眼) / fix6(修好)。
第二行 = 对应的走路姿势（说明腿交叉也仍然修好了）。"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
W = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
     r"\Ilyich-Genshin-Test-Version\.workbuddy")

ROW1 = [
    ("no-align (eyes OK / legs crossed)", os.path.join(W, "vysna_final", "preview_EYEF0_front.png")),
    ("fix5  (legs OK / eyes SHUT)", os.path.join(W, "vysna_fix5", "preview_EYELE_front_le.png")),
    ("fix6  (eyes OK + legs OK)", os.path.join(W, "vysna_fix6", "preview_EYE6_front.png")),
]
ROW2 = [
    ("walk f12 : no-align", os.path.join(HERE, "_posetest", "W4_f12_front.png")),
    ("walk f12 : fix5", os.path.join(HERE, "_posetest", "W5_f12_front.png")),
    ("walk f12 : fix6", os.path.join(HERE, "_posetest", "W6_f12_front.png")),
]

CW, CH = 400, 420
HDR = 22


def load(p):
    im = Image.open(p).convert("RGB")
    im.thumbnail((CW, CH), Image.LANCZOS)
    c = Image.new("RGB", (CW, CH), (26, 26, 30))
    c.paste(im, ((CW - im.width) // 2, (CH - im.height) // 2))
    return c


sheet = Image.new("RGB", (CW * 3, (CH + HDR) * 2), (18, 18, 22))
d = ImageDraw.Draw(sheet)
for row, items in enumerate((ROW1, ROW2)):
    for i, (tag, p) in enumerate(items):
        if not os.path.exists(p):
            continue
        sheet.paste(load(p), (i * CW, row * (CH + HDR) + HDR))
        d.text((i * CW + 6, row * (CH + HDR) + 5), tag, fill=(255, 235, 120))
p = os.path.join(HERE, "_posetest", "DELIVER_eye_fix.png")
sheet.save(p)
print("->", p, sheet.size)

# -*- coding: utf-8 -*-
"""交付对照图：颈部特写（三版）+ 走路姿势（两版）。

标签用 ASCII —— PIL 自带位图字体不含中文，写中文会变方块。
"""
import os

from PIL import Image, ImageDraw

S = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(S, "_posetest")
BG = (244, 245, 248)
FG = (24, 26, 34)

# (标签, 图片相对 scripts 的路径, 裁剪框)
NECK_ROWS = [
    ("1. no bind-conform  (legs cross when walking)", "../vysna_final/preview_N0_left.png"),
    ("2. old conform: per-bone constant  -> neck torn", "../vysna_fix4/preview_N4_left.png"),
    ("3. new conform: continuous chain curve  (FIXED)", "../vysna_fix5/preview_N5_left.png"),
]
NECK_CROP = (150, 60, 300, 260)

WALK_ROWS = [
    ("4. BEFORE  walk f12 (old)", "_posetest/W4_f12_front.png"),
    ("5. AFTER   walk f12 (new)", "_posetest/W5_f12_front.png"),
]
WALK_CROP = (140, 180, 330, 560)          # 走路图是 460x700


def tile(rel, crop, scale=2):
    im = Image.open(os.path.join(S, rel)).convert("RGB").crop(crop)
    return im.resize((im.width * scale, im.height * scale), Image.LANCZOS)


def main():
    gap, pad_top, pad_bot = 12, 30, 12
    col_label_w = 0
    A = [tile(r, NECK_CROP, 2) for _l, r in NECK_ROWS]
    B = [tile(r, WALK_CROP, 2) for _l, r in WALK_ROWS]

    def row(tiles, labels, y0):
        nonlocal col_label_w
        x = gap
        maxh = 0
        for (lab, t) in zip(labels, tiles):
            dr.text((x + 4, y0 - 22), lab, fill=FG)
            sheet.paste(t, (x, y0))
            dr.rectangle([x - 1, y0 - 1, x + t.width, y0 + t.height], outline=(160, 162, 172))
            x += t.width + gap
            maxh = max(maxh, t.height)
        return y0 + maxh + gap + 22

    wA = sum(t.width for t in A) + gap * (len(A) + 1)
    wB = sum(t.width for t in B) + gap * (len(B) + 1)
    W = max(wA, wB)
    hA = max(t.height for t in A)
    hB = max(t.height for t in B)
    H = pad_top + hA + gap + 30 + hB + pad_bot
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)

    dr.text((gap, 9), "VYSNA  neck / neckline  -  bind-conform fix", fill=FG)
    y = pad_top
    y = row(A, [l for l, _r in NECK_ROWS], y)
    y = row(B, [l for l, _r in WALK_ROWS], y)

    p = os.path.join(OUT, "DELIVER_neck_fix.png")
    n = 2
    while True:
        try:
            sheet.save(p)
            break
        except PermissionError:
            p = os.path.join(OUT, "DELIVER_neck_fix_%d.png" % n)
            n += 1
    print("-> %s (%dx%d)" % (p, sheet.width, sheet.height))


if __name__ == "__main__":
    main()

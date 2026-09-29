# -*- coding: utf-8 -*-
"""列出 HOI4 步兵动画里每根骨的 s（缩放）取值 —— 找出「被隐藏」的骨。"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_render as PR  # noqa: E402

ANIMS = [
    ("moving_rifle", r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
                     r"\gfx\models\units\GER_infantry_moving_rifle.anim"),
    ("march_rifle", r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
                    r"\gfx\models\units\GER_infantry_march_rifle.anim"),
]
HERE = os.path.dirname(os.path.abspath(__file__))
out = []
W = out.append

for tag, ap in ANIMS:
    if not os.path.exists(ap):
        W("## %s 不存在" % tag)
        continue
    fps, frames, abones, samples = PR.load_anim(ap)
    slot, counts = PR.channel_slots(abones)
    W("=" * 70)
    W("## %s  fps=%.2f frames=%d 骨数=%d" % (tag, fps, frames, len(abones)))
    W("=" * 70)
    zero, other = [], []
    for i, b in enumerate(abones):
        if "s" not in b["sa"]:
            other.append((b["name"], "无s通道", b["sa"]))
            continue
        o = slot[i]["s"]
        vals = [float(samples["s"][f * counts["s"] + o]) for f in range(frames)]
        mn, mx = min(vals), max(vals)
        if mx < 1e-6:
            zero.append((b["name"], b["sa"], mn, mx))
        elif abs(mn - 1.0) > 1e-4 or abs(mx - 1.0) > 1e-4:
            other.append((b["name"], "s=%.4f~%.4f" % (mn, mx), b["sa"]))
    W("")
    W("★ s 恒为 0（= 该动画里被隐藏 / 缩没的骨）  共 %d 根：" % len(zero))
    for nm, sa, mn, mx in zero:
        W("    %-22s sa=%r  s=[%.4f,%.4f]" % (nm, sa, mn, mx))
    W("")
    W("· s 非常量 1（有缩放动画）  共 %d 根：" % len(other))
    for nm, d, sa in other:
        W("    %-22s %-24s sa=%r" % (nm, d, sa))

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_anim_scales.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_anim_scales_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt)
print("\n->", p)

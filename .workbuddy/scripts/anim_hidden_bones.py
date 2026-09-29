# -*- coding: utf-8 -*-
"""扫描一批 HOI4 步兵动画，统计每根骨「s 恒为 0（被隐藏）」的情况。
目的：确认该把翅膀挂到哪根骨上才在所有动画里都可见。
"""
import glob
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_render as PR  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
DIRS = [os.path.join(GAME, r"gfx\models\units")]

# 只看德国步兵那一族（我们的实体用的就是 GER_infantry_*）
files = sorted(glob.glob(os.path.join(DIRS[0], "GER_infantry*.anim")))
# 再补几个通用的
files += sorted(glob.glob(os.path.join(DIRS[0], "*.anim")))[:0]

out = []
W = out.append
W("扫描 %d 个动画文件" % len(files))
W("")

zero_cnt = defaultdict(list)   # 骨名 -> [文件名...]
err = []
for fp in files:
    try:
        fps, frames, abones, samples = PR.load_anim(fp)
        slot, counts = PR.channel_slots(abones)
        for i, b in enumerate(abones):
            if "s" not in b["sa"]:
                continue
            o = slot[i]["s"]
            vals = samples["s"][o::counts["s"]][:frames]
            if len(vals) and float(np.max(vals)) < 1e-6:
                zero_cnt[b["name"]].append(os.path.basename(fp))
    except Exception as e:  # noqa: BLE001
        err.append((os.path.basename(fp), repr(e)))

W("★ 在多少 / %d 个动画里被隐藏（s 恒 0）：" % len(files))
for nm in sorted(zero_cnt, key=lambda k: -len(zero_cnt[k])):
    W("    %-22s %2d 个动画" % (nm, len(zero_cnt[nm])))
W("")
W("· 全程「从未被隐藏」的关键躯干骨检查：")
for nm in ("back_mid", "Hip", "head", "Root", "Chest"):
    n = len(zero_cnt.get(nm, []))
    W("    %-22s 被隐藏 %d 次  ->  %s" % (nm, n, "安全" if n == 0 else "★危险"))
if err:
    W("")
    W("读不动的文件 %d 个：" % len(err))
    for a, b in err[:10]:
        W("    %s  %s" % (a, b))
W("")
W("被隐藏的骨明细（前 40 个动画）：")
for fp in files[:40]:
    try:
        fps, frames, abones, samples = PR.load_anim(fp)
        slot, counts = PR.channel_slots(abones)
        zs = []
        for i, b in enumerate(abones):
            if "s" not in b["sa"]:
                continue
            o = slot[i]["s"]
            vals = samples["s"][o::counts["s"]][:frames]
            if len(vals) and float(np.max(vals)) < 1e-6:
                zs.append(b["name"])
        W("    %-46s %s" % (os.path.basename(fp), ",".join(zs) if zs else "(无)"))
    except Exception:  # noqa: BLE001
        pass

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_anim_hidden_bones.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_anim_hidden_bones_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt)
print("\n->", p)

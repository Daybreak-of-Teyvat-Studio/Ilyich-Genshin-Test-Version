# -*- coding: utf-8 -*-
"""为什么 mid_back_node 驱动的顶点会塌缩成一点？逐项拆解。"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pose_render as PR  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MESH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "../vysna_fix2/Vysna_infantry.mesh")
ANIM = (r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
        r"\gfx\models\units\GER_infantry_moving_rifle.anim")
TARGETS = (sys.argv[2].split(",") if len(sys.argv) > 2
           else ["mid_back_node", "Hip", "head", "back_mid"])
REFF = (r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry\PRC_infantry.mesh")

out = []
W = out.append


def anl(M, label):
    d = float(np.linalg.det(M[:3, :3]))
    W("        %-22s max|a|=%.4g  det=%.4g  t=(%.3f,%.3f,%.3f)"
      % (label, np.abs(M).max(), d, M[0, 3], M[1, 3], M[2, 3]))


for mpath, tag in ((MESH, "VYSNA"), (REFF, "PRC_REF")):
    if not os.path.exists(mpath):
        W("== %s 不存在：%s" % (tag, mpath))
        continue
    bones, geoms = PR.load_mesh(mpath)
    names = [b[0] for b in bones]
    W("=" * 78)
    W("== %s   %s" % (tag, os.path.basename(mpath)))
    W("=" * 78)
    for t in TARGETS:
        if t not in names:
            W("  [%s] 骨架里没有" % t)
            continue
        i = names.index(t)
        nm, pa, invb = bones[i]
        W("  [%s] idx=%d pa=%s" % (t, i, pa if pa is not None and pa >= 0 else "无"))
        if pa is not None and pa >= 0:
            W("      父骨 = %s" % bones[pa][0])
        anl(invb, "tx (=inv_bind)")
        try:
            bl = np.linalg.inv(invb)
            anl(bl, "bind (tx^-1)")
        except np.linalg.LinAlgError:
            W("        bind 求逆失败（奇异）")

    # 动画侧
    fps, frames, abones, samples = PR.load_anim(ANIM)
    slot, counts = PR.channel_slots(abones)
    aidx = {}
    for k, b in enumerate(abones):
        aidx.setdefault(b["name"], k)
    W("  动画: fps=%.2f frames=%d 骨数=%d  通道计数 t=%d q=%d s=%d"
      % (fps, frames, len(abones), counts["t"], counts["q"], counts["s"]))
    for t in TARGETS:
        ai = aidx.get(t)
        if ai is None:
            W("  [%s] 动画里没有这根骨" % t)
            continue
        b = abones[ai]
        sl = slot[ai]
        W("  [%s] anim idx=%d sa=%r slots=%s" % (t, ai, b["sa"], sl))
        for f in (0, 6, 12):
            line = "      f%-3d " % f
            if "t" in sl:
                o = (f * counts["t"] + sl["t"]) * 3
                line += "t=(%.4f,%.4f,%.4f) " % tuple(samples["t"][o:o + 3])
            else:
                line += "t=-- "
            if "q" in sl:
                o = (f * counts["q"] + sl["q"]) * 4
                line += "q=(%.4f,%.4f,%.4f,%.4f) " % tuple(samples["q"][o:o + 4])
            else:
                line += "q=-- "
            if "s" in sl:
                o = f * counts["s"] + sl["s"]
                line += "s=%.4f" % float(samples["s"][o])
            else:
                line += "s=--"
            W(line)

    # 实际摆姿势后该骨的 world / skin
    geoms2 = []
    for g in geoms:
        g2 = dict(g)
        g2["P"] = g["P"].copy()
        if g.get("N") is not None:
            g2["N"] = g["N"].copy()
        geoms2.append(g2)
    PR.pose(bones, geoms2, ANIM, 0)
    W("  --- 摆完 f0 后，各目标的顶点云 ---")
    for t in TARGETS:
        if t not in names:
            continue
        gi = names.index(t)
        for k, g in enumerate(geoms):
            if "ix" not in g:
                continue
            arg = np.argmax(g["w"], axis=1)
            dom = g["ix"][np.arange(len(g["ix"])), arg]
            sel = (dom == gi) & (g["w"].max(1) > 1e-6)
            if sel.sum() < 10:
                continue
            p0 = g["P"][sel]
            p1 = geoms2[k]["P"][sel]
            W("      [%s] geoms#%d n=%d  bind size=(%.2f,%.2f,%.2f) -> f0 size=(%.2f,%.2f,%.2f)"
              % (t, k, int(sel.sum()),
                 *(p0.max(0) - p0.min(0)), *(p1.max(0) - p1.min(0))))

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_wing_diag.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_wing_diag_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt)
print("\n->", p)

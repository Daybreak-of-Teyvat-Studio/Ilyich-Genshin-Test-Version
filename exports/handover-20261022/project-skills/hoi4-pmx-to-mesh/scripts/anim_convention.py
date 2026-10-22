# -*- coding: utf-8 -*-
"""找出 .anim 的正确读法：四元数分量顺序 × 采样排列顺序。

判据：按公式算出各骨的世界位置，看哪一组能得到「解剖学上合理」的结果
  · LeftToeBase / RightToeBase 的 y 应接近 0~1（踩地）
  · head 的 y 应约 5~7
  · 左右脚尖的 x 应为相反数、且 |x| 约 0.3~1.3
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdx_data import read_meshfile  # noqa: E402
from pose_render import load_mesh, load_anim, read_tx  # noqa: E402

MESH = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
        r"\gfx\models\units\DOT_Keqing\Keqing_infantry.mesh")
ANIM = (r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
        r"\gfx\models\units\GER_infantry_moving_rifle.anim")

bones, geoms = load_mesh(MESH)
fps, frames, abones, samples = load_anim(ANIM)


def qmat(q, order):
    if order == "xyzw":
        x, y, z, w = q
    else:
        w, x, y, z = q
    n = x * x + y * y + z * z + w * w
    if n < 1e-12:
        return np.eye(3)
    s = 2.0 / n
    return np.array([
        [1 - s * (y * y + z * z), s * (x * y - z * w), s * (x * z + y * w)],
        [s * (x * y + z * w), 1 - s * (x * x + z * z), s * (y * z - x * w)],
        [s * (x * z - y * w), s * (y * z + x * w), 1 - s * (x * x + y * y)]])


def m4(R, t):
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = t
    return M


def world_positions(order, layout, frame=0):
    """layout: 'bone' = 骨主序（k*frames+f）; 'frame' = 帧主序（f*nb+k）"""
    nb = len(abones)
    has_t = [i for i, b in enumerate(abones) if "t" in b["sa"]]
    has_q = [i for i, b in enumerate(abones) if "q" in b["sa"]]
    slot_t = {b: k for k, b in enumerate(has_t)}
    slot_q = {b: k for k, b in enumerate(has_q)}

    binds = [np.linalg.inv(b[2]) for b in bones]
    rest_local = []
    for i, (nm, pa, invb) in enumerate(bones):
        rest_local.append(binds[i] if (pa is None or pa < 0)
                          else np.linalg.inv(binds[pa]) @ binds[i])
    aidx = {}
    for i, b in enumerate(abones):
        aidx.setdefault(b["name"], i)

    world = []
    for i, (nm, pa, invb) in enumerate(bones):
        ai = aidx.get(nm)
        if ai is None or abones[ai]["sa"] == "":
            L = rest_local[i]
        else:
            if ai in slot_t:
                k = slot_t[ai]
                o = (3 * (k * frames + frame) if layout == "bone"
                     else 3 * (frame * len(has_t) + k))
                t = samples["t"][o:o + 3]
            else:
                t = rest_local[i][:3, 3]
            if ai in slot_q:
                k = slot_q[ai]
                o = (4 * (k * frames + frame) if layout == "bone"
                     else 4 * (frame * len(has_q) + k))
                R = qmat(samples["q"][o:o + 4], order)
            else:
                R = rest_local[i][:3, :3]
            L = m4(R, t)
        world.append(L if (pa is None or pa < 0) else world[pa] @ L)

    pos = {}
    for i, (nm, pa, invb) in enumerate(bones):
        pos[nm] = world[i][:3, 3]
    return pos


print("帧数 %d，动画骨 %d 根" % (frames, len(abones)))
print("Hip frame0 t =", samples["t"][0:3])
print()
KEYS = ["Hip", "head", "LeftFoot", "LeftToeBase", "RightToeBase", "LeftHand"]
print("%-8s %-8s | %s" % ("四元数", "采样序", "  ".join("%-22s" % k for k in KEYS)))
for order in ("xyzw", "wxyz"):
    for layout in ("bone", "frame"):
        p = world_positions(order, layout, 0)
        row = []
        for k in KEYS:
            v = p.get(k)
            row.append("(%6.2f,%6.2f,%6.2f)" % tuple(v) if v is not None else "-")
        print("%-8s %-8s | %s" % (order, layout, "  ".join("%-22s" % r for r in row)))

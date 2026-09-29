# -*- coding: utf-8 -*-
"""对比 MOD 内各角色 .mesh 的尺度归一化情况：顶点 Y 范围 + 骨架关键骨世界坐标。
结论用于确定 Vysna 实体的 scale 取值。只读。"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa: E402

ROOT = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
MINE = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out\Vysna_infantry.mesh")

TARGETS = [
    os.path.join(ROOT, r"gfx\models\units\DOT_Keqing\Keqing_infantry.mesh"),
    os.path.join(ROOT, r"gfx\models\units\DOT_Amber\Amber_infantry.mesh"),
    os.path.join(ROOT, r"gfx\models\units\DOT_Furina\Furina_infantry.mesh"),
    os.path.join(ROOT, r"gfx\models\units\DOT_Kokomi\Kokomi_infantry.mesh"),
    os.path.join(ROOT, r"gfx\models\units\DOT_Citlali\Citlali_infantry.mesh"),
    os.path.join(ROOT, r"gfx\models\units\DOT_Gorou\wulang.mesh"),
    os.path.join(ROOT, r"gfx\models\units\DOT_models\Odetta_infantry.mesh"),
    MINE,
]


def mesh_nodes(node):
    res = []
    if node.tag == "mesh":
        res.append(node)
    for ch in node:
        res.extend(mesh_nodes(ch))
    return res


def bone_world(shape):
    """从 shape 下 skeleton/bone 的 tx (列主序 3x4 逆绑定矩阵) 反解世界位置。"""
    out = {}
    sk = None
    for ch in shape:
        if ch.tag == "skeleton":
            sk = ch
    if sk is None:
        return out
    bi = None
    for ch in sk:
        if ch.tag == "bones":
            bi = ch.get("ix", [])
    # 骨架节点顺序里骨架名表在 shape 的某个子节点，这里靠 ix 与 bone 出现顺序对应
    names = []
    for ch in shape:
        if ch.tag == "skeleton":
            for g in ch:
                if g.tag == "node":
                    names.append(g.get("name"))
    idx = 0
    for ch in sk:
        if ch.tag != "bone":
            continue
        tx = np.array(ch.get("tx", []), dtype=np.float64)
        if tx.size != 12:
            idx += 1
            continue
        cols = tx.reshape(4, 3)
        R = np.column_stack([cols[0], cols[1], cols[2]])
        t = cols[3]
        try:
            pos = -R.T @ t
        except Exception:  # noqa: BLE001
            pos = np.array([np.nan] * 3)
        nm = names[idx] if idx < len(names) else "?"
        out[nm] = pos
        idx += 1
    return out


def analyse(path):
    root = read_meshfile(path)
    meshes = mesh_nodes(root)
    ys = []
    for m in meshes:
        p = np.array(m.get("p", []), dtype=np.float64)
        if p.size:
            ys.append(p.reshape(-1, 3)[:, 1])
    y = np.concatenate(ys) if ys else np.zeros(0)
    # 取第一个 shape 的骨架
    shape = None
    for ch in root:
        if ch.tag == "shape":
            shape = ch
            break
    if shape is None:
        for ch in root:
            for g in ch:
                if g.tag == "shape":
                    shape = g
    bw = bone_world(shape) if shape is not None else {}
    return y, bw


rows = []
for p in TARGETS:
    tag = os.path.basename(p)
    if not os.path.exists(p):
        rows.append("%-34s MISSING" % tag)
        continue
    try:
        y, bw = analyse(p)
    except Exception as e:  # noqa: BLE001
        rows.append("%-34s ERROR %s" % (tag, e))
        continue
    head = bw.get("head", np.array([np.nan] * 3))
    hip = bw.get("Hip", np.array([np.nan] * 3))
    toe = bw.get("LeftToeBase", np.array([np.nan] * 3))
    rows.append("%-34s  Y[%7.3f,%7.3f]  head.y=%7.3f  Hip.y=%6.3f  Toe.y=%6.3f  骨骼=%d"
                % (tag, y.min(), y.max(), head[1], hip[1], toe[1], len(bw)))

txt = ("各角色 mesh 的顶点 Y 范围与骨架关键骨世界 Y（判定尺度是否统一）\n"
       + "=" * 118 + "\n" + "\n".join(rows)
       + "\n\n注：若各模型 head.y 一致，说明都归一到同一 HOI4 骨架，scale 只是美术取向。\n"
       + "    参考：原版 infantry_rifle_entity scale=0.8，Keqing_infantry_entity scale=0.85。\n")
print(txt)

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_scale_calib")
path = base + ".txt"
i = 2
while os.path.exists(path):
    path = "%s_%d.txt" % (base, i)
    i += 1
with open(path, "w", encoding="utf-8") as f:
    f.write(txt)
print("-> %s" % path)

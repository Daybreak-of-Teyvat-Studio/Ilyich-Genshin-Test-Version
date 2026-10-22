# -*- coding: utf-8 -*-
"""骨架 / 网格一致性体检。

回答一个关键问题：
  「能正常跑动画的同类模型，它们的网格有没有对齐到骨架的 rest 位置？」

做法：
  1. 从每个 .mesh 的 <skeleton> 解出每根骨的 rest 位置（由 tx 反解）。
  2. 从每个 mesh 节点的 skin 解出每个顶点的**主骨**，统计落在每根骨上的
     顶点质心。
  3. 输出「骨位置 <-> 顶点质心」的距离。

如果同类模型的距离都很小（< 0.15 左右），说明它们都做过 bind pose 对齐；
如果距离普遍很大，说明它们也没对齐（那我们的问题就另有原因）。
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa: E402

BASE = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
        r"\gfx\models\units")
PRC = r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry\PRC_infantry.mesh"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "report_rig_check.txt")

MODELS = [
    ("PRC_infantry", PRC),
    ("Keqing", os.path.join(BASE, "DOT_Keqing", "Keqing_infantry.mesh")),
    ("Amber", os.path.join(BASE, "DOT_Amber", "Amber_infantry.mesh")),
    ("Furina", os.path.join(BASE, "DOT_Furina", "Furina_infantry.mesh")),
    ("Kokomi", os.path.join(BASE, "DOT_Kokomi", "Kokomi_infantry.mesh")),
    ("Citlali", os.path.join(BASE, "DOT_Citlali", "Citlali_infantry.mesh")),
    ("Vysna(ours)", os.path.join(BASE, "DOT_Vysna", "Vysna_infantry.mesh")),
]

KEY = ["Hip", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
       "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase",
       "back_mid", "LeftForeArm", "LeftHand", "head", "mid_back_node"]

L = []
P = L.append


def decompose_tx(tx):
    """tx 是列主序 3x4 的逆绑定矩阵 -> (R, t)。rest 位置 = -R.T @ t。"""
    cols = np.asarray(tx, np.float64).reshape(4, 3)
    R = cols[:3].T
    t = cols[3]
    return R, t


def load(path):
    root = read_meshfile(path)
    bones = []          # 按 skeleton 顺序
    for obj in root:
        for shape in obj:
            sk = shape.find("skeleton")
            if sk is not None:
                for b in sk:
                    R, t = decompose_tx(b.get("tx"))
                    pos = -R.T @ t
                    pa = b.get("pa")
                    bones.append(dict(name=b.tag, pos=pos,
                                      parent=(pa[0] if pa else -1)))
    # 每个 mesh 节点的顶点主骨
    verts = []
    tris = 0
    for obj in root:
        for shape in obj:
            for m in shape.findall("mesh"):
                if "p" not in m.attrib:
                    continue
                p = np.array(m.get("p"), np.float64).reshape(-1, 3)
                tris += len(m.get("tri", [])) // 3
                sk = m.find("skin")
                if sk is None or not sk.get("ix"):
                    verts.append((p, np.zeros(len(p), np.int64)))
                    continue
                # ★ pdx_data 文档：skin.bones = "num skin influences"（标量，本模型=4），
                #   skin.ix = 骨骼 id（**全局骨骼索引**，不是相对列表的下标）。
                idx = np.array(sk.get("ix"), np.int64).reshape(-1, 4)
                w = np.array(sk.get("w"), np.float64).reshape(-1, 4)
                arg = np.argmax(w, axis=1)
                dom = idx[np.arange(len(idx)), arg]
                dom = np.where(np.arange(4)[arg] < 0, -1, dom)
                # 全 0 权重的顶点视为未绑定
                dom = np.where(w.max(1) > 1e-6, dom, -1)
                verts.append((p, dom))
    return bones, verts, tris


def stats(model):
    path = model[1]
    if not os.path.isfile(path):
        P("  !! 缺文件 %s" % path)
        return None
    bones, verts, tris = load(path)
    p = np.concatenate([v[0] for v in verts], 0)
    d = np.concatenate([v[1] for v in verts], 0)
    cent = {}
    cnt = {}
    for i, bn in enumerate(bones):
        sel = d == i
        c = int(sel.sum())
        cnt[bn["name"]] = c
        if c >= 20:
            cent[bn["name"]] = p[sel].mean(0)
    return dict(name=model[0], bones=bones, cent=cent, cnt=cnt, tris=tris,
                bbox=(p.min(0), p.max(0)), nv=len(p))


P("=" * 78)
P("骨架 / 网格一致性体检")
P("=" * 78)

res = {}
for m in MODELS:
    r = stats(m)
    if r:
        res[r["name"]] = r

# ---------- 1) 各模型骨架是否一致 ----------
P("")
P("【1】各模型骨架 rest 位置 vs PRC_infantry")
ref = {b["name"]: b["pos"] for b in res["PRC_infantry"]["bones"]}
P("    %-14s %s" % ("模型", "   ".join("%-11s" % k[:11] for k in KEY[:7])))
for name, r in res.items():
    row = []
    for k in KEY[:7]:
        b = next((x for x in r["bones"] if x["name"] == k), None)
        if b is None or k not in ref:
            row.append("%-11s" % "-")
            continue
        row.append("%-11.3f" % np.linalg.norm(b["pos"] - ref[k]))
    P("    %-14s %s" % (name, "   ".join(row)))
P("    （数值 = 与 PRC 同名骨 rest 位置的距离；0 = 完全一致）")

# ---------- 2) 骨位置 <-> 顶点质心 ----------
P("")
P("【2】骨 rest 位置 <-> 该骨主导顶点的质心  的距离")
for name, r in res.items():
    P("")
    P("    --- %s   顶点 %d  三角 %d  bbox X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]"
      % (name, r["nv"], r["tris"], r["bbox"][0][0], r["bbox"][1][0],
         r["bbox"][0][1], r["bbox"][1][1], r["bbox"][0][2], r["bbox"][1][2]))
    P("        %-14s %6s   %-22s %-22s %6s" % ("骨", "顶点数", "骨位置", "顶点质心", "距离"))
    for k in KEY:
        b = next((x for x in r["bones"] if x["name"] == k), None)
        if b is None:
            continue
        c = r["cent"].get(k)
        if c is None:
            P("        %-14s %6d   %-22s %-22s" % (k, r["cnt"].get(k, 0), "-", "-"))
            continue
        P("        %-14s %6d   (%6.3f,%6.3f,%6.3f)   (%6.3f,%6.3f,%6.3f)  %6.3f"
          % (k, r["cnt"].get(k, 0), b["pos"][0], b["pos"][1], b["pos"][2],
             c[0], c[1], c[2], np.linalg.norm(b["pos"] - c)))

# ---------- 3) 汇总 ----------
P("")
P("【3】汇总：每根骨的「骨位置-顶点质心」距离（有顶点落在其上的骨）")
P("    %-14s %s" % ("模型", " ".join("%6s" % k[:6] for k in KEY)))
for name, r in res.items():
    row = []
    for k in KEY:
        b = next((x for x in r["bones"] if x["name"] == k), None)
        c = r["cent"].get(k)
        if b is None or c is None:
            row.append("%6s" % "-")
        else:
            row.append("%6.3f" % np.linalg.norm(b["pos"] - c))
    P("    %-14s %s" % (name, " ".join(row)))

txt = "\n".join(L)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
print("\n-> " + OUT)

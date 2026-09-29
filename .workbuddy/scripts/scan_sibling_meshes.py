# -*- coding: utf-8 -*-
"""统计 MOD 内各角色步兵 .mesh 的规模，作为减面决策基线。只读。"""
import os
import sys

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa: E402

ROOT = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
TARGETS = [
    r"gfx\models\units\DOT_Keqing\Keqing_infantry.mesh",
    r"gfx\models\units\DOT_Amber\Amber_infantry.mesh",
    r"gfx\models\units\DOT_Furina\Furina_infantry.mesh",
    r"gfx\models\units\DOT_Kokomi\Kokomi_infantry.mesh",
    r"gfx\models\units\DOT_Citlali\Citlali_infantry.mesh",
    r"gfx\models\units\DOT_Gorou\wulang.mesh",
    r"gfx\models\units\DOT_Yoimiya\Yoimiya_infantry.mesh",
    r"gfx\models\units\DOT_models\Odetta_infantry.mesh",
]

out = []


def walk(node, depth=0):
    """收集所有 mesh 节点（含嵌套 shape 下的）。"""
    res = []
    if node.tag == "mesh":
        res.append(node)
    for ch in node:
        res.extend(walk(ch, depth + 1))
    return res


def count_tris(mesh_node):
    tot_tri = 0
    tot_v = 0
    tri_counts = []
    for ch in mesh_node:
        if ch.tag != "p":
            continue
        n = int(ch.get("count", "0") or 0)
        tot_v = n
    # tri 属性在 mesh 节点自身
    for name, val in mesh_node.attrib.items():
        pass
    return tot_v


for rel in TARGETS:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        out.append("MISSING  %s" % rel)
        continue
    try:
        root = read_meshfile(p)
    except Exception as e:  # noqa: BLE001
        out.append("ERROR    %s  %s" % (rel, e))
        continue
    meshes = walk(root)
    nv = 0
    nt = 0
    mats = 0
    for m in meshes:
        # p / tri 等是 mesh 节点的「属性」，值即数据数组；material 是子节点
        nv += len(m.get("p", []) or []) // 3
        nt += len(m.get("tri", []) or []) // 3
        mats += sum(1 for ch in m if ch.tag == "material")
    out.append("%-46s size=%9d  verts=%6d  tris=%6d  meshnodes=%d  mats=%d"
               % (rel.split("\\")[-1], os.path.getsize(p), nv, nt, len(meshes), mats))

# 本地产物对比
mine = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out\Vysna_infantry.mesh")
out.append("-" * 100)
out.append("【待接入】Vysna_infantry.mesh  59,065 顶点 / 75,119 三角 / 4 mesh")

txt = "\n".join(out)
print(txt)

# 本项目工作区禁止覆盖已存在文件 → 自动避让命名
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_sibling_meshes")
path = base + ".txt"
i = 2
while os.path.exists(path):
    path = "%s_%d.txt" % (base, i)
    i += 1
with open(path, "w", encoding="utf-8") as f:
    f.write(txt + "\n")
print("\n-> %s" % path)

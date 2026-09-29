# -*- coding: utf-8 -*-
"""从 PRC_infantry.mesh 反推 HOI4 标准骨架的 rest 世界位置。

tx 是每骨骼的 *inverse bind matrix*（3x4，世界->骨骼），
对其求逆即得骨骼的绑定变换，平移列就是骨骼在绑定姿态下的世界位置。
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa

ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
OUT = os.path.join(ROOT, ".workbuddy", "report_hoi4_rig2.txt")

srcs = [
    ("PRC_infantry", ".workbuddy/vysna_work/PRC_infantry/PRC_infantry.mesh"),
    ("Keqing", "Daybreak of Teyvat Gamma Version/gfx/models/units/DOT_Keqing/Keqing_infantry.mesh"),
]

L = []
def P(s=""):
    L.append(str(s))

P("=" * 78)
P("HOI4 标准骨架 rest 位置（tx 求逆后的平移列）")
P("=" * 78)

rigs = {}
for tag, rel in srcs:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    root = read_meshfile(p)
    obj = root.find("object")
    sk = None
    for shape in obj:
        sk = shape.find("skeleton")
        if sk is not None:
            break
    if sk is None:
        P(f"{tag}: 无 skeleton")
        continue
    rows = []
    for b in sk:
        tx = b.get("tx")
        if not tx:
            rows.append((b.tag, None, None))
            continue
        # ★ tx 是 **列主序** 存储的 3x4 矩阵：4 个列向量，每个 3 个 float。
        #   col0..col2 = 旋转矩阵 R 的三列，col3 = 平移 t。
        #   tx 是 inverse bind matrix（世界->骨骼），求逆得骨骼绑定变换，
        #   其平移列就是骨骼在 rest 姿态下的世界位置： pos = -Rᵀ · t
        cols = np.array(tx, dtype=np.float64).reshape(4, 3)
        R = np.column_stack([cols[0], cols[1], cols[2]])
        t = cols[3]
        pos = -R.T @ t
        pa = b.get("pa")
        pa = pa[0] if isinstance(pa, list) else pa
        rows.append((b.tag, pa, pos))
    rigs[tag] = rows

    P("")
    P(f"--- {tag}  ({len(rows)} 骨骼) ---")
    P(f"  {'i':>3} {'name':<24}{'parent':<22}{'rest pos (x, y, z)'}")
    for i, (nm, pa, pos) in enumerate(rows):
        if pos is None:
            P(f"  {i:>3} {nm:<24}{str(pa):<22}<无 tx>")
        else:
            P(f"  {i:>3} {nm:<24}{str(pa):<22}({pos[0]:8.4f}, {pos[1]:8.4f}, {pos[2]:8.4f})")

# 比较两个骨架
P("")
P("=" * 78)
P("两套骨架位置差异（应为同规格）")
P("=" * 78)
if len(rigs) == 2:
    (t1, r1), (t2, r2) = list(rigs.items())
    d = {}
    for nm, pa, pos in r2:
        d[nm] = pos
    maxd = 0.0
    for nm, pa, pos in r1:
        if pos is None or nm not in d or d[nm] is None:
            continue
        dd = float(np.abs(pos - d[nm]).max())
        maxd = max(maxd, dd)
        if dd > 1e-4:
            P(f"  {nm:<24} {t1}={np.round(pos,4)}  {t2}={np.round(d[nm],4)}  Δ={dd:.5f}")
    P(f"  逐骨骼最大分量差 = {maxd:.6f}  -> {'一致' if maxd < 1e-3 else '不一致'}")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("OK ->", OUT, len(L), "lines")

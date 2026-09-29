# -*- coding: utf-8 -*-
"""测量已有角色 mesh 的规模 + PRC_infantry 骨骼空间位置。"""
import os
import sys

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa

ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
OUT = os.path.join(ROOT, ".workbuddy", "report_mesh_scale.txt")

TARGETS = [
    ("参考 PRC_infantry", ".workbuddy/vysna_work/PRC_infantry/PRC_infantry.mesh"),
    ("团队 Keqing", "Daybreak of Teyvat Gamma Version/gfx/models/units/DOT_Keqing/Keqing_infantry.mesh"),
    ("团队 Amber", ".backups/DOT_Amber_01/anbo_sd.mesh"),
]

L = []
def P(s=""):
    L.append(str(s))

P("=" * 78)
P("A. 已有角色 mesh 规模对比")
P("=" * 78)
P(f"{'模型':<22}{'文件大小':>12}{'shape':>7}{'材质':>6}{'顶点':>9}{'三角形':>9}{'骨骼':>7}  shader")
for tag, rel in TARGETS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        P(f"{tag:<22}  <不存在> {p}")
        continue
    root = read_meshfile(p)
    obj = root.find("object")
    nshape = 0
    tot_v = tot_t = tot_m = 0
    bones = 0
    shaders = []
    if obj is not None:
        for shape in obj:
            nshape += 1
            if shape.tag.lower().startswith("p") and "cube" in shape.tag.lower():
                continue
            for mesh in shape.findall("mesh"):
                pv = mesh.get("p")
                if pv:
                    tot_v += len(pv) // 3
                tv = mesh.get("tri")
                if tv:
                    tot_t += len(tv) // 3
                tot_m += len(mesh.findall("material"))
                for mate in mesh.findall("material"):
                    sh = mate.get("shader")
                    shaders.append(sh[0] if isinstance(sh, list) and sh else str(sh))
            sk = shape.find("skeleton")
            if sk is not None:
                bones += len(list(sk))
    P(f"{tag:<22}{os.path.getsize(p):>12,}{nshape:>7}{tot_m:>6}{tot_v:>9,}{tot_t:>9,}{bones:>7}  {shaders[:2]}")

P("")
P("=" * 78)
P("B. PRC_infantry 骨骼空间位置（从 tx 3x4 矩阵取平移列）")
P("=" * 78)
p = os.path.join(ROOT, ".workbuddy", "vysna_work", "PRC_infantry", "PRC_infantry.mesh")
root = read_meshfile(p)
obj = root.find("object")
for shape in obj:
    sk = shape.find("skeleton")
    if sk is None:
        continue
    P(f"shape <{shape.tag}>  骨骼 {len(list(sk))} 根")
    P(f"  {'idx':>4} {'name':<24}{'parent':<22}{'tx 平移 (x, y, z)'}")
    for i, b in enumerate(sk):
        ix = b.get("ix")
        ix = ix[0] if isinstance(ix, list) else ix
        pa = b.get("pa")
        pa = pa[0] if isinstance(pa, list) else pa
        tx = b.get("tx")
        if tx:
            # 3x4 行主序：平移在 [3], [7], [11]
            P(f"  {str(ix):>4} {b.tag:<24}{str(pa):<22}({tx[3]:8.3f}, {tx[7]:8.3f}, {tx[11]:8.3f})")
        else:
            P(f"  {str(ix):>4} {b.tag:<24}{str(pa):<22}<无 tx>")
    break

P("")
P("=" * 78)
P("C. PRC_infantry 材质与贴图")
P("=" * 78)
for shape in obj:
    for mesh in shape.findall("mesh"):
        for mate in mesh.findall("material"):
            P(f"  shader={mate.get('shader')}")
            P(f"    diff={mate.get('diff')}")
            P(f"    n   ={mate.get('n')}")
            P(f"    spec={mate.get('spec')}")
        sk = mesh.find("skin")
        if sk is not None:
            P(f"  skin.bones={sk.get('bones')}  ix_len={len(sk.get('ix') or [])}  w_len={len(sk.get('w') or [])}")

P("")
P("=" * 78)
P("D. locator")
P("=" * 78)
loc = root.find("locator")
if loc is not None:
    for nd in loc:
        P(f"  <{nd.tag}>  p={nd.get('p')}  q={nd.get('q')}  pa={nd.get('pa')}  tx={'有' if nd.get('tx') else '无'}")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("OK ->", OUT, len(L), "lines")

# -*- coding: utf-8 -*-
"""对比 dump 多个 .mesh：规模、材质、骨架。"""
import os
import sys

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa

ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
FILES = [
    r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry\PRC_infantry.mesh",
    os.path.join(ROOT, "Daybreak of Teyvat Gamma Version", "gfx", "models", "units",
                 "DOT_Keqing", "Keqing_infantry.mesh"),
]

L = []


def P(s=""):
    L.append(str(s))
    print(s)


for f in FILES:
    P("=" * 78)
    P(os.path.basename(f) + "   " + ("%d bytes" % os.path.getsize(f) if os.path.isfile(f) else "缺失"))
    if not os.path.isfile(f):
        continue
    root = read_meshfile(f)
    for obj in root:
        P("  object %s attr=%s" % (obj.tag, {k: v for k, v in obj.attrib.items()}))
        for shape in obj:
            P("    shape %s attr=%s" % (shape.tag, {k: v for k, v in shape.attrib.items()}))
            for child in shape:
                if child.tag == "mesh":
                    nv = len(child.attrib.get("p", [])) // 3
                    nt = len(child.attrib.get("tri", [])) // 3
                    P("      mesh 顶点=%d 三角=%d 属性=%s" % (nv, nt, list(child.attrib.keys())))
                    for sub in child:
                        if sub.tag == "material":
                            P("        material %s" % {k: v for k, v in sub.attrib.items()})
                        elif sub.tag == "skin":
                            P("        skin bones=%s ix=%d w=%d" % (
                                sub.attrib.get("bones"), len(sub.attrib.get("ix", [])),
                                len(sub.attrib.get("w", []))))
                        elif sub.tag == "aabb":
                            P("        aabb min=%s max=%s" % (
                                [round(x, 3) for x in sub.attrib.get("min", [])],
                                [round(x, 3) for x in sub.attrib.get("max", [])]))
                elif child.tag == "skeleton":
                    bones = list(child)
                    P("      skeleton 骨骼数=%d" % len(bones))
                    P("        序列: %s" % ", ".join(b.tag for b in bones))

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_ref_compare.txt"),
     "w", encoding="utf-8").write("\n".join(L))

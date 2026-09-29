# -*- coding: utf-8 -*-
"""用 io_pdx_mesh 的 pdx_data 解析 PRC_infantry.mesh，dump 结构实例。"""
import os
import sys

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa

ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
OUT = os.path.join(ROOT, ".workbuddy", "report_mesh_dump.txt")

L = []
def P(s=""):
    L.append(str(s))

def show_prop(el, name, maxn=8):
    v = el.get(name)
    if v is None:
        P(f"      {name}: <无>")
        return None
    if isinstance(v, list):
        P(f"      {name}: len={len(v)}  head={[round(x, 4) if isinstance(x, float) else x for x in v[:maxn]]}")
        return v
    P(f"      {name}: {v!r}")
    return v

for fn in ["PRC_infantry.mesh", ]:
    path = os.path.join(ROOT, ".workbuddy", "vysna_work", "PRC_infantry", fn)
    P("=" * 78)
    P(f"### {fn}  ({os.path.getsize(path):,} bytes)")
    P("=" * 78)
    root = read_meshfile(path)
    P(f"root tag = {root.tag}")
    P(f"root attrs = {dict(root.attrib)}")
    P("")

    def walk(el, depth=0):
        ind = "  " * depth
        props = []
        for k, v in el.attrib.items():
            if isinstance(v, list):
                props.append(f"{k}[{len(v)}]")
            else:
                props.append(f"{k}={v!r}")
        P(f"{ind}<{el.tag}>  {' '.join(props)}")
        if el.tag == "mesh":
            for k in ("p", "n", "ta", "u0", "u1", "tri"):
                show_prop(el, k)
            for sub in el:
                if sub.tag == "aabb":
                    show_prop(sub, "min")
                    show_prop(sub, "max")
                elif sub.tag == "material":
                    for k in ("shader", "diff", "n", "spec"):
                        show_prop(sub, k)
                elif sub.tag == "skin":
                    show_prop(sub, "bones")
                    show_prop(sub, "ix", maxn=12)
                    show_prop(sub, "w", maxn=12)
        elif el.tag == "bone":
            show_prop(el, "ix")
            show_prop(el, "pa")
            show_prop(el, "tx", maxn=12)
        elif el.tag == "node":
            for k in ("p", "q", "pa", "tx"):
                show_prop(el, k)
        for c in el:
            walk(c, depth + 1)

    walk(root)

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("OK ->", OUT, len(L), "lines")

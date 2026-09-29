# -*- coding: utf-8 -*-
"""用 pdx_data 解析 PRC_infantry.mesh，dump 结构 + 抽取 skeleton 块备用。"""
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa

REF = r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry\PRC_infantry.mesh"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\scripts\report_ref_mesh.txt"

# read_meshfile 直接返回 root Element（不落盘）
root = read_meshfile(REF)
L = []
P = L.append

P("ROOT tag=%s attrib=%s" % (root.tag, dict(root.attrib)))
P("")


def dump(el, depth=0):
    ind = "  " * depth
    attrs = []
    for k, v in el.attrib.items():
        if isinstance(v, (list, tuple)):
            attrs.append("%s<%s>[%d] %s" % (k, type(v).__name__, len(v),
                                            str(v[:8]) + ("..." if len(v) > 8 else "")))
        else:
            attrs.append("%s=%r" % (k, v))
    P("%s<%s> %s   children=%d" % (ind, el.tag, " ".join(attrs), len(list(el))))
    for c in el:
        dump(c, depth + 1)


dump(root)
text = "\n".join(L)
open(OUT, "w", encoding="utf-8").write(text)
print(text[:6000])

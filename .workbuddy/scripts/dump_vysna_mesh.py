# -*- coding: utf-8 -*-
"""dump Vysna_infantry.mesh 的完整结构（shape / mesh / material / skin / skeleton），
用于确认贴图引用名与 shader 是否与 HOI4 约定一致。只读。"""
import os
import sys

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa: E402

MESH = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out\Vysna_infantry.mesh")

root = read_meshfile(MESH)
out = []
out.append("root tag=%s attrs=%s" % (root.tag, list(root.attrib.keys())))
out.append("mod=%s ver=%s" % (root.get("mod"), root.get("version")))


def walk(node, depth=0):
    pad = "  " * depth
    # 只打印关键属性，数组类属性只报长度
    info = []
    for k, v in node.attrib.items():
        if isinstance(v, (list, tuple)):
            info.append("%s=len%d" % (k, len(v)))
        else:
            info.append("%s=%s" % (k, v))
    out.append("%s<%s> %s" % (pad, node.tag, " ".join(info)))
    for ch in node:
        walk(ch, depth + 1)


walk(root)

# 逐 mesh 打印材质 / aabb 的实际值
out.append("")
for i, ch in enumerate(root.iter()):
    if ch.tag != "mesh":
        continue
    for g in ch:
        if g.tag == "material":
            vals = {}
            for k, v in g.attrib.items():
                s = v if isinstance(v, str) else (v[0] if len(v) else None)
                vals[k] = s
            out.append("mesh[%d] material  shader=%s  diff=%s  n=%s  spec=%s"
                       % (len([1 for _ in []]) or 0, vals.get("shader"), vals.get("diff"),
                          vals.get("n"), vals.get("spec")))
        if g.tag == "aabb":
            out.append("        aabb min=%s max=%s" % (g.get("min"), g.get("max")))
        if g.tag == "skin":
            out.append("        skin bones=%s  ix_len=%d" % (g.get("bones"), len(g.get("ix", []))))

# 打印 object / shape 名字
for ch in root:
    out.append("object name=%r" % (ch.tag,))
    for g in ch:
        out.append("  shape name=%r attrs=%s" % (g.tag, list(g.attrib.keys())))

# 逐 mesh 展开材质
n = 0
for ch in root.iter():
    if ch.tag == "mesh":
        n += 1
out.append("")
out.append("mesh 节点数 = %d" % n)

txt = "\n".join(out)
print(txt)
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_vysna_mesh_struct")
path = base + ".txt"
i = 2
while os.path.exists(path):
    path = "%s_%d.txt" % (base, i)
    i += 1
with open(path, "w", encoding="utf-8") as f:
    f.write(txt + "\n")
print("-> %s" % path)

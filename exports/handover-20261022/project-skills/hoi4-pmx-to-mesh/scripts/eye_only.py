# -*- coding: utf-8 -*-
"""把 face 组里眼部相关材质逐个单独渲染，各存一张图（同取景，便于比对）。"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_preview as RP  # noqa

V = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out12"
MESH = os.path.join(V, "Vysna_infantry.mesh")
OUT = os.path.join(V, "_eyetest")
os.makedirs(OUT, exist_ok=True)

W, H = 900, 900
ZOOM = 9.0
FY = 6.72

nodes = RP.gather(MESH)
print("mesh 节点：", [os.path.basename(str(n["diff"])) for n in nodes])
fi = next(i for i, n in enumerate(nodes) if "face" in str(n["diff"]).lower())
nd = nodes[fi]
P, T, UV = nd["P"], nd["T"], nd["UV"]

# 复现 vysna_build 的材质分段：tri 的排列 = 被保留的 face 组材质顺序
EXCLUDE = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s", "裙+", "颜3", "颜4"]
FACE_MATS = ["口舌", "星目", "白目", "目", "目光", "眉", "睫", "瞳", "颜", "颜2", "鼻线", "齿"]
KEEP = [m for m in FACE_MATS if not any(k in m for k in EXCLUDE)]

# 用 face 组的三角数推断每材质占用区间（与 build 的 grp_faces 顺序一致：
# grp_faces 按 PMX 材质顺序 append，这里按 PMX 顺序过滤）
import pmx_parse
pmx = pmx_parse.PMX(r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳\薇斯纳.pmx")
order = []
for m in pmx.materials:
    nm = m["name"]
    if nm not in FACE_MATS:
        continue
    if any(k in nm for k in EXCLUDE):
        continue
    order.append((nm, m["face_count"] // 3))

acc = 0
seg = {}
for nm, n in order:
    seg[nm] = (acc, n)
    acc += n
print("face 组三角分段：", {k: v for k, v in seg.items()}, "合计", acc, "mesh 三角", len(T))


def panel(cols):
    nd2 = dict(nd)
    # 保留被选中的三角，其余丢掉
    keep = np.zeros(len(T), bool)
    for nm in cols:
        a, n = seg[nm]
        keep[a:a + n] = True
    nd2["T"] = T[keep]
    return list(nodes[:fi]) + [nd2] + list(nodes[fi + 1:])


for nm in KEEP:
    img = RP.render(panel([nm]), V, W, H, RP.VIEWS["front"], zoom=ZOOM, focus_y=FY, cull=False)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 460, 20], fill=(0, 0, 0))
    d.text((5, 4), "only %s  (%d tri)" % (nm, seg[nm][1]), fill=(255, 235, 120))
    p = os.path.join(OUT, "ONLY_%s.png" % nm)
    im.save(p)
    print("->", p, im.size)

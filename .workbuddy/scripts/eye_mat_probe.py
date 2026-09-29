# -*- coding: utf-8 -*-
"""查清眼部各材质：贴图指向、UV 范围、几何朝向、材质顺序、以及图集里的实际内容。"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pmx_parse import PMX                      # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
ATLAS = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
         r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out3\vysna_face_atlas.png")

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
UV = np.array(pmx.v_uv, np.float64)
faces = np.array(pmx.faces, np.int64)

out = []
acc = 0
EYE = ["白目", "目", "瞳", "目光", "星目", "睫", "眉", "颜", "颜2"]

out.append("眼部相关材质逐项体检（材质顺序 = 绘制顺序）")
out.append("=" * 100)
out.append("%-4s %-6s %-16s %8s %8s %-22s %-22s %s"
           % ("idx", "名", "贴图", "前景", "双面", "u 范围", "v 范围", "draw_flag"))
for i, mt in enumerate(pmx.materials):
    nm = mt["name"]
    st, cnt = acc, mt["face_count"]
    acc += cnt
    if nm not in EYE:
        continue
    ti = mt["tex"]
    tp = pmx.textures[ti] if 0 <= ti < len(pmx.textures) else "?"
    f = faces[st:st + cnt].ravel()
    u = UV[f, 0]
    v = UV[f, 1]
    flags = mt["draw_flag"]
    out.append("%-4d %-6s %-16s %8d %8s %-22s %-22s 0x%02x%s%s%s"
               % (i, nm, os.path.basename(tp), cnt // 3,
                  "是" if (flags & 0x01) else "否",
                  "[%.3f, %.3f]" % (u.min(), u.max()),
                  "[%.3f, %.3f]" % (v.min(), v.max()),
                  flags,
                  " 双面" if flags & 0x01 else "",
                  " 描边" if flags & 0x10 else "",
                  " 顶点色" if flags & 0x20 else ""))

out.append("")
out.append("材质完整顺序（只列 face 组，显示绘制先后）：")
acc = 0
k = 0
for i, mt in enumerate(pmx.materials):
    nm = mt["name"]
    st, cnt = acc, mt["face_count"]
    acc += cnt
    if nm in ("白目", "目", "瞳", "目光", "星目", "睫", "眉", "颜", "颜2",
              "鼻线", "口舌", "齿"):
        out.append("   #%02d  %-4s  三角 %5d" % (i, nm, cnt // 3))
        k += 1

# ---- 各贴图在 UV 空间的实际占比（可见率）
out.append("")
out.append("眼部贴图内容检查（源图）：")
for nm in ["白目", "目", "瞳", "目光", "星目"]:
    for mt in pmx.materials:
        if mt["name"] != nm:
            continue
        ti = mt["tex"]
        tp = pmx.textures[ti].replace("\\", os.sep).replace("/", os.sep)
        full = os.path.join(SRC, tp)
        im = Image.open(full).convert("RGBA")
        a = np.asarray(im, np.uint8)
        vis = a[..., 3] > 128
        rgb = a[..., :3][vis] if vis.any() else np.zeros((1, 3), np.uint8)
        out.append("   %-4s %-14s %4dx%-4d 不透明占比 %5.1f%%  可见区 RGB 均值 %s"
                   % (nm, os.path.basename(tp), im.width, im.height,
                      vis.mean() * 100,
                      tuple(int(x) for x in rgb.mean(0))))
        break

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_eye_mats.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_eye_mats_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % p)

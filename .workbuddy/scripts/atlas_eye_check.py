# -*- coding: utf-8 -*-
"""独立复核：面部分组图集里，眼球材质（目/瞳/白目/目光）的 UV 落到哪块区域、
采样出来是什么颜色。与「直接采源贴图」逐点对比，定位是否为图集映射 bug。"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pmx_parse import PMX  # noqa: E402
import vysna_build as VB  # noqa: E402

OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out3"

pmx = PMX(os.path.join(VB.SRC, "薇斯纳.pmx"))
V = np.array(pmx.v_pos, np.float64)
UV = np.array(pmx.v_uv, np.float64)

# 重建面部分组的材质 / 贴图清单（与 vysna_build 的口径一致）
rng = []
acc = 0
for i, mt in enumerate(pmx.materials):
    rng.append((i, acc, mt["face_count"]))
    acc += mt["face_count"]

keep = [i for i, mt in enumerate(pmx.materials)
        if not any(k in mt["name"] for k in VB.EXCLUDE_KEYS)]

faces_face = []
mats_face = set()
for i, st, cnt in rng:
    if i not in keep:
        continue
    nm = pmx.materials[i]["name"]
    if VB.MAT_GROUP.get(nm) != "face":
        continue
    mats_face.add(nm)
    for k in range(st, st + cnt):
        faces_face.append((i, pmx.faces[k]))

tis = sorted({pmx.materials[i]["tex"] for i, _ in faces_face})
print("face 组材质:", sorted(mats_face))
print("face 组贴图索引:", tis, [os.path.basename(pmx.textures[t]) for t in tis])

logs = []
atlas, place = VB.build_atlas(tis, pmx, 512, lambda s: logs.append(str(s)), "face")
AH, AW = atlas.shape[0], atlas.shape[1]
print("图集 %dx%d   放置: %s" % (AW, AH,
      {os.path.basename(pmx.textures[k]): v[:4] for k, v in place.items()}))

out = []
out.append("眼球材质图集取样复核（atlas %dx%d）" % (AW, AH))
out.append("=" * 104)
out.append("%-8s %-10s %10s %10s %10s   %s" % ("材质", "贴图", "源图均值", "图集均值", "最大通道差", "判定"))
out.append("-" * 104)

# 源贴图缓存
srcc = {}


def src_tex(ti):
    if ti not in srcc:
        p = os.path.join(VB.SRC, pmx.textures[ti].replace("\\", os.sep))
        im = Image.open(p)
        im = VB.resize_keep_aspect(im, 512)
        srcc[ti] = np.asarray(im.convert("RGBA"), np.uint8)
    return srcc[ti]


for mi, mt in enumerate(pmx.materials):
    nm = mt["name"]
    if nm not in ("目", "瞳", "白目", "目光", "颜", "睫"):
        continue
    ti = mt["tex"]
    X, Y, cw, ch, tw, th = place[ti]
    src = src_tex(ti)
    st = None
    for i2, s2, c2 in rng:
        if i2 == mi:
            st, c2_ = s2, c2
    idx = np.array(pmx.faces[st:st + c2_], np.int64)
    uv = UV[idx]
    # 图集取样
    au = np.clip((X + VB.GUTTER + np.mod(uv[:, 0], 1.0) * tw).astype(int), 0, AW - 1)
    av = np.clip((Y + VB.GUTTER + np.mod(uv[:, 1], 1.0) * th).astype(int), 0, AH - 1)
    got = atlas[av, au]
    # 源图取样（同尺寸）
    su = np.clip((np.mod(uv[:, 0], 1.0) * src.shape[1]).astype(int), 0, src.shape[1] - 1)
    sv = np.clip((np.mod(uv[:, 1], 1.0) * src.shape[0]).astype(int), 0, src.shape[0] - 1)
    exp = src[sv, su]
    d = np.abs(got.astype(int) - exp.astype(int)).max()
    out.append("%-8s %-10s RGB%s  RGB%s  %10d   %s"
               % (nm, os.path.basename(pmx.textures[ti]),
                  tuple(got[:, :3].mean(0).round(0).astype(int)),
                  tuple(exp[:, :3].mean(0).round(0).astype(int)),
                  d, "一致" if d <= 2 else "!! 不一致"))
    out.append("         图集 cell X=%d Y=%d w=%d h=%d  贴图内区 %dx%d   alpha 均值 图集=%.1f 源=%.1f"
               % (X, Y, cw, ch, tw, th, got[:, 3].mean(), exp[:, 3].mean()))

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_atlas_eye_check.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_atlas_eye_check_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % p)

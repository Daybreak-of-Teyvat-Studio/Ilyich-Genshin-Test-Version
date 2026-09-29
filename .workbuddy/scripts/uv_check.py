# -*- coding: utf-8 -*-
"""UV 重映射正确性校验。

对转换器用到的每个顶点：分别用「原始 UV 采样原始贴图」和「重映射 UV 采样图集」，
逐点比较颜色差。若中位差很小，说明图集与 UV 重映射无误。
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pmx_parse import PMX                      # noqa: E402
import vysna_build as vb                       # noqa: E402

OUT = os.path.join(HERE, "report_uv_check.txt")
L = []
P = L.append


def sample_nn(tex, uv):
    H, W = tex.shape[0], tex.shape[1]
    u = np.mod(uv[:, 0], 1.0)
    v = np.mod(uv[:, 1], 1.0)
    x = np.clip((u * W).astype(np.int64), 0, W - 1)
    y = np.clip((v * H).astype(np.int64), 0, H - 1)
    return tex[y, x].astype(np.int32)


pmx = PMX(os.path.join(vb.SRC, "薇斯纳.pmx"))
UV = np.array(pmx.v_uv, np.float64)

# 复现转换器里的图集与 placement
atlases = {}
for g in sorted(set(vb.MAT_GROUP.values())):
    tis = sorted({pmx.materials[i]["tex"] for i, m in enumerate(pmx.materials)
                  if vb.MAT_GROUP.get(m["name"]) == g and 0 <= m["tex"] < len(pmx.textures)})
    atlas, place = vb.build_atlas(tis, pmx, vb.GROUP_CAP[g], lambda *a: None, g)
    atlases[g] = (atlas, place)

rng = np.random.default_rng(7)
rng_num = int(os.environ.get("UVCHECK_N", "2000"))
total = []
for i, mt in enumerate(pmx.materials):
    g = vb.MAT_GROUP.get(mt["name"])
    if g is None:
        continue
    ti = mt["tex"]
    atlas, place = atlases[g]
    X, Y, cw, ch, tw, th = place[ti]
    AH, AW = atlas.shape[0], atlas.shape[1]

    # 还原原始贴图（与 build_atlas 同样的缩放）
    path = pmx.textures[ti].replace("\\", os.sep).replace("/", os.sep)
    im = Image.open(os.path.join(vb.SRC, path))
    im = vb.resize_keep_aspect(im, vb.GROUP_CAP[g])
    orig = np.asarray(im.convert("RGBA"), np.uint8)

    # 该材质区间抽若干顶点
    st = sum(pmx.materials[k]["face_count"] for k in range(i))
    ids = np.unique(np.array(pmx.faces[st:st + mt["face_count"]], np.int64))
    if len(ids) == 0:
        continue
    pick = rng.choice(ids, size=min(rng_num, len(ids)), replace=False)

    u0 = UV[pick]
    c_orig = sample_nn(orig, u0)
    # 重映射
    u = np.mod(u0[:, 0], 1.0)
    v = np.mod(u0[:, 1], 1.0)
    mu = (X + vb.GUTTER + u * tw) / AW
    mv = (Y + vb.GUTTER + v * th) / AH
    c_atlas = sample_nn(atlas, np.stack([mu, mv], 1))

    d = np.abs(c_orig - c_atlas).max(1)
    # 逐通道平均差
    md = np.abs(c_orig - c_atlas).mean()
    total.append(d)
    P("  %-8s tex[%2d] %-22s 顶点 %6d  逐点最大通道差 中位 %5.1f  P90 %5.1f  均值 %.2f"
      % (mt["name"], ti, os.path.basename(pmx.textures[ti]), len(pick),
         np.median(d), np.percentile(d, 90), md))

alld = np.concatenate(total)
P("")
P("汇总：采样 %d 个顶点（占全部 UV 的抽样）" % len(alld))
P("  最大通道差  中位 %.2f  P90 %.2f  P99 %.2f  max %.2f"
  % (np.median(alld), np.percentile(alld, 90), np.percentile(alld, 99), alld.max()))
P("  判定：%s" % ("通过（中位差 <= 2，说明 UV 重映射与原贴图一致）"
                if np.median(alld) <= 2 else "**异常，需排查**"))

txt = "\n".join(L)
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)

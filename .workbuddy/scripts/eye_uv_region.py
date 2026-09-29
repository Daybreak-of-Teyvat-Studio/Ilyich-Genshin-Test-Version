# -*- coding: utf-8 -*-
"""把眼部材质的 UV 三角形投影回源贴图（按构建时的映射 mod+翻转），
肉眼判断采样区是否落在「眼睛」该在的位置。

同时打印三角重心的采样颜色，用于确认取到的是不是眼珠。"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pmx_parse import PMX                                    # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
TEX = os.path.join(SRC, "tex")

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
UV = np.array(pmx.v_uv, np.float64)
F = np.array(pmx.faces, np.int64).reshape(-1)

segs, acc = [], 0
for mt in pmx.materials:
    cnt = mt["face_count"] // 3
    segs.append((mt["name"], acc, cnt, mt.get("tex", "")))
    acc += cnt
byname = {s[0]: s for s in segs}

EYE = ["白目", "目", "瞳", "目光", "星目"]
print("眼部材质分段：")
for nm in EYE:
    _, a, c, ti = byname[nm]
    f = F[3 * a:3 * (a + c)]
    u, v = UV[f, 0], UV[f, 1]
    print("  %-4s tri=%4d  tex=%-14s  u[%+.4f,%+.4f]  v[%+.4f,%+.4f]"
          % (nm, c, ti, u.min(), u.max(), v.min(), v.max()))


def draw(texname, marks, S=560):
    """marks: [(材质名, 颜色, 面索引数组)]"""
    im = Image.open(os.path.join(TEX, texname)).convert("RGBA")
    W, H = im.size
    base = Image.new("RGB", (W, H), (250, 250, 250))
    base.paste(im, (0, 0), im)
    base = base.resize((S, S), Image.LANCZOS)
    d = ImageDraw.Draw(base)
    for nm, col, f in marks:
        u = np.mod(UV[f, 0], 1.0)
        v = np.mod(UV[f, 1], 1.0)
        ok = np.ones(len(u), bool)
        T = np.stack([u, v], 1).reshape(-1, 3, 2)
        for t in T:
            pts = [(p[0] * S, (1.0 - p[1]) * S) for p in t]
            d.polygon(pts, outline=col)
        # 包围盒
        d.rectangle([u.min() * S, (1 - v.max()) * S,
                     u.max() * S, (1 - v.min()) * S], outline=col, width=3)
    return base


def faces_of(nm):
    _, a, c, _ = byname[nm]
    return F[3 * a:3 * (a + c)]


tiles = [
    draw("目.png", [("目", (255, 0, 0), faces_of("目"))]),
    draw("瞳.png", [("瞳", (255, 0, 0), faces_of("瞳"))]),
    draw("颜.png", [("白目", (255, 0, 0), faces_of("白目")),
                    ("星目", (170, 0, 255), faces_of("星目"))]),
]
S = tiles[0].width
sheet = Image.new("RGB", (S * 3, S), (255, 255, 255))
for i, t in enumerate(tiles):
    sheet.paste(t, (i * S, 0))
p = os.path.join(HERE, "report_eye_uv_region.png")
sheet.save(p)
print("\n-> %s   (左: 目.png 中: 瞳.png 右: 颜.png 红=白目 紫=星目)" % p)


def sample(texname, f, mode):
    a = np.array(Image.open(os.path.join(TEX, texname)).convert("RGBA"))
    H, W = a.shape[:2]
    u, v = UV[f, 0].copy(), UV[f, 1].copy()
    if mode == "mod":
        u, v = np.mod(u, 1.0), np.mod(v, 1.0)
    elif mode == "neg":
        v = np.abs(v)
    x = np.clip((u * W).astype(int), 0, W - 1)
    y = np.clip(((1.0 - v) * H).astype(int), 0, H - 1)
    return a[y, x]


print("\n重心采样（按不同 v 处理假设）：")
for nm in EYE:
    _, a, c, ti = byname[nm]
    f = faces_of(nm)
    for mode in ("mod", "neg"):
        px = sample(ti, f, mode)
        rgb = px[:, :3].mean(0)
        al = px[:, 3].mean() / 255.0
        print("  %-4s %-4s  平均 RGB=(%3d,%3d,%3d)  平均 alpha=%.3f"
              % (nm, mode, rgb[0], rgb[1], rgb[2], al))

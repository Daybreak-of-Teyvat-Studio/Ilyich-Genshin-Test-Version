# -*- coding: utf-8 -*-
"""直接从 PMX 渲染，用于判定「叠层材质」的设计意图。

输出三联对比图：
  A. MMD 风格 —— 材质顺序绘制 + alpha 混合（不透明层写深度，半透明层只混合）
  B. 深度 <  —— 模拟 D3D LESS（重合时先画的赢）
  C. 深度 <= —— 模拟 D3D LESS_EQUAL（重合时后画的赢，HOI4 常见默认）

用 --mats 指定参与渲染的材质名（逗号分隔，支持子串匹配），便于隔离单层。
"""
import argparse
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmx_parse import PMX  # noqa: E402

# 与 vysna_build 一致的骨架对齐参数（源坐标 -> HOI4 单位）
S = 0.389774
R = np.array([[1.0, 0.0, 0.0],
              [0.0, 0.9985, 0.0544],
              [0.0, -0.0544, 0.9985]])
T = np.array([0.0, -0.0614, 0.4709])

VIEWS = {"front": (math.pi / 2, 0.10), "q34": (math.pi / 2 - 0.6, 0.14)}

# 材质 ID 伪色（用于定位“哪个材质在 <= 规则下胜出”）
PALETTE = [(230, 60, 60), (60, 190, 90), (70, 120, 240), (235, 200, 60),
           (200, 80, 210), (60, 210, 210), (245, 140, 50), (150, 150, 160),
           (120, 80, 40), (255, 255, 255), (0, 90, 60), (90, 0, 120),
           (255, 170, 200), (140, 255, 170), (170, 170, 255), (255, 120, 120),
           (120, 255, 120), (120, 120, 255), (255, 255, 120), (200, 0, 255),
           (0, 255, 200), (255, 0, 120), (100, 100, 0), (0, 100, 100),
           (100, 0, 100), (60, 60, 60), (230, 230, 230), (170, 100, 20),
           (20, 170, 100), (20, 100, 170), (170, 20, 100), (100, 20, 170),
           (170, 170, 20), (20, 170, 170), (170, 20, 20), (40, 200, 60),
           (200, 60, 40), (60, 40, 200), (200, 200, 100)]


def load_tex(path):
    with Image.open(path) as im:
        return np.asarray(im.convert("RGBA"), np.uint8).copy()


def build(src, keep, exclude=()):
    p = PMX(os.path.join(src, "薇斯纳.pmx"))
    V = np.array(p.v_pos, np.float64)
    N = np.array(p.v_nrm, np.float64)
    UV = np.array(p.v_uv, np.float64)
    F = np.array(p.faces, np.int64)
    texs = p.textures

    Vh = S * (R @ V.T).T + T

    tris = []          # (mat_index, mat_name, i0,i1,i2)
    cur = 0
    for mi, m in enumerate(p.materials):
        nm = m["name"]
        n = m["face_count"]
        if exclude and any(k in nm for k in exclude):
            cur += n
            continue
        if keep and not any(k in nm for k in keep):
            cur += n
            continue
        for k in range(cur, cur + n, 3):
            tris.append((mi, nm, F[k], F[k + 1], F[k + 2]))
        cur += n

    texcache = {}

    def tex_of(mi):
        ti = p.materials[mi]["tex"]
        if ti < 0 or ti >= len(texs):
            return None
        rel = texs[ti].replace("\\", os.sep)
        if rel not in texcache:
            fp = os.path.join(src, rel)
            texcache[rel] = load_tex(fp) if os.path.isfile(fp) else None
        return texcache[rel]

    return Vh, N, UV, tris, tex_of, p


def render(Vh, UV, tris, tex_of, W, H, view, zoom, focus, mode):
    az, el = view
    ca, sa, ce, se = math.cos(az), math.sin(az), math.cos(el), math.sin(el)
    fwd = np.array([ca * ce, se, sa * ce]); fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array([0.0, 1.0, 0.0])); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    c = np.array(focus, np.float64)
    scale = min(W, H) / (2.0 * 0.55) * zoom

    img = np.zeros((H, W, 4), np.float64)
    img[:, :, :3] = 0.09
    img[:, :, 3] = 1.0
    zbuf = np.full((H, W), 1e18)
    light = -fwd + 0.45 * up + 0.30 * right
    light /= np.linalg.norm(light)

    for mi, nm, i0, i1, i2 in tris:
        tex = tex_of(mi)
        if tex is None:
            continue
        th, tw = tex.shape[:2]
        P = Vh[[i0, i1, i2]]
        rel = P - c
        px = W / 2 + (rel @ right) * scale
        py = H / 2 - (rel @ up) * scale
        zs = rel @ fwd
        minx, maxx = int(np.floor(px.min())), int(np.ceil(px.max()))
        miny, maxy = int(np.floor(py.min())), int(np.ceil(py.max()))
        minx = max(minx, 0); maxx = min(maxx, W - 1)
        miny = max(miny, 0); maxy = min(maxy, H - 1)
        if minx > maxx or miny > maxy:
            continue
        x0, y0, x1, y1, x2, y2 = px[0], py[0], px[1], py[1], px[2], py[2]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(minx, maxx + 1) + 0.5,
                             np.arange(miny, maxy + 1) + 0.5)
        w0 = ((x1 - gx) * (y2 - gy) - (x2 - gx) * (y1 - gy)) / area
        w1 = ((x2 - gx) * (y0 - gy) - (x0 - gx) * (y2 - gy)) / area
        w2 = 1.0 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        u = w0 * UV[i0, 0] + w1 * UV[i1, 0] + w2 * UV[i2, 0]
        v = w0 * UV[i0, 1] + w1 * UV[i1, 1] + w2 * UV[i2, 1]
        tx = np.clip((u % 1.0 * tw).astype(np.int64), 0, tw - 1)
        ty = np.clip((v % 1.0 * th).astype(np.int64), 0, th - 1)
        texel = tex[ty, tx].astype(np.float64) / 255.0
        al = texel[:, :, 3]
        lam = 0.32 + 0.75 * 0.6      # 固定亮度：面部层次判定不需要光照干扰
        col = np.clip(texel[:, :, :3] * lam, 0, 1)
        if mode == "matid":
            # 按材质号上伪色，alpha 视为不透明 —— 用来定位“谁赢了这个像素”。
            # 注意着色数组要和纹理路径一样是「子图」形状 (H_sub, W_sub, 3)。
            c = np.array(PALETTE[mi % len(PALETTE)], np.float64) / 255.0
            col = np.broadcast_to(c, texel.shape[:2] + (3,)).copy()
            al = np.ones(texel.shape[:2])

        subz = zbuf[miny:maxy + 1, minx:maxx + 1]
        subi = img[miny:maxy + 1, minx:maxx + 1]
        yy, xx = np.nonzero(inside)
        zz = z[yy, xx]
        cc = col[yy, xx]
        aa = al[yy, xx]

        if mode == "mmd":
            # 不透明：深度测试通过则写入颜色+深度；半透明：混合但不写深度
            op = aa >= 0.985
            tr = ~op
            if op.any():
                sy, sx = yy[op], xx[op]
                sel = zz[op] < subz[sy, sx]
                sy, sx = sy[sel], sx[sel]
                subz[sy, sx] = zz[op][sel]
                subi[sy, sx, :3] = cc[op][sel]
                subi[sy, sx, 3] = 1.0
            if tr.any():
                sy, sx = yy[tr], xx[tr]
                sel = zz[tr] <= subz[sy, sx]
                sy, sx = sy[sel], sx[sel]
                a2 = aa[tr][sel][:, None]
                subi[sy, sx, :3] = cc[tr][sel] * a2 + subi[sy, sx, :3] * (1 - a2)
        else:
            le = (mode == "le")
            sel = inside & ((z <= subz) if le else (z < subz))
            if not sel.any():
                continue
            sy, sx = np.nonzero(sel)
            subz[sy, sx] = z[sy, sx]
            subi[sy, sx, :3] = col[sy, sx]
            subi[sy, sx, 3] = 1.0

    return (img[:, :, :3] * 255).astype(np.uint8)


def label(img, txt):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 175, 22], fill=(0, 0, 0))
    d.text((6, 6), txt, fill=(255, 235, 120))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳")
    ap.add_argument("--mats", default="")
    ap.add_argument("--exclude", default="结晶,头饰,照れ,袜s,翼+",
                    help="排除的材质名（子串匹配），默认与 vysna_build 的 EXCLUDE_KEYS 一致")
    ap.add_argument("--matid", action="store_true",
                    help="改为输出「材质号伪色」单面板（按 <= 规则），用于定位胜出材质")
    ap.add_argument("--view", default="front")
    ap.add_argument("--w", type=int, default=460)
    ap.add_argument("--h", type=int, default=460)
    ap.add_argument("--zoom", type=float, default=9.0)
    ap.add_argument("--focus", default="0,6.66,-1.0")
    ap.add_argument("--out", default=r"C:\Users\XIANGZIYUAN\vysna_work\_layer_probe.png")
    args = ap.parse_args()

    keep = [s for s in args.mats.split(",") if s]
    excl = [s for s in args.exclude.split(",") if s]
    Vh, N, UV, tris, tex_of, p = build(args.src, keep, excl)
    print("参与材质筛选: %s  排除: %s -> 三角 %d" % (keep or "(全部)", excl, len(tris)))
    fx, fy, fz = [float(x) for x in args.focus.split(",")]
    view = VIEWS[args.view]
    if args.matid:
        used = sorted({mi for mi, nm, a, b, c in tris})
        print("\n材质号伪色图例（%d 个材质参与）：" % len(used))
        for mi in used:
            c = PALETTE[mi % len(PALETTE)]
            print("   idx %-3d %-8s  RGB(%3d,%3d,%3d)" % (mi, p.materials[mi]["name"], *c))
        a = render(Vh, UV, tris, tex_of, args.w, args.h, view,
                   args.zoom, (fx, fy, fz), "matid")
        panels = [label(a, "material-id winner under <=")]
    else:
        panels = []
        for mode, cap in (("mmd", "A MMD-style (alpha blend, mat order)"),
                          ("lt", "B depth < (first wins)"),
                          ("le", "C depth <= (last wins)")):
            a = render(Vh, UV, tris, tex_of, args.w, args.h, view,
                       args.zoom, (fx, fy, fz), mode)
            panels.append(label(a, cap))
    cv = Image.new("RGB", (args.w * len(panels) + 4 * (len(panels) - 1), args.h),
                   (12, 12, 12))
    for i, pn in enumerate(panels):
        cv.paste(pn, (i * (args.w + 4), 0))
    base, ext = os.path.splitext(args.out)
    path = args.out
    i = 2
    while os.path.exists(path):
        path = "%s_%d%s" % (base, i, ext)
        i += 1
    cv.save(path)
    print("-> %s  %s" % (path, cv.size))


if __name__ == "__main__":
    main()

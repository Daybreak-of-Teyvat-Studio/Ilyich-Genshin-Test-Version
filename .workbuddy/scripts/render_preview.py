# -*- coding: utf-8 -*-
"""把 HOI4 .mesh + DDS 用纯 numpy 做软件光栅化，输出预览 PNG 用于目视验证。

能同时验证：几何是否合理、三角绕序/背面剔除是否正确、UV 映射是否对、
贴图是否接对、蒙皮绑定是否落在正确骨骼上（可选按骨骼着色模式）。

用法：
    python render_preview.py <mesh> <outdir> [--w 480] [--h 900] [--bone-shade]
"""
import argparse
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa: E402


def load_dds(path):
    """PIL 能读 DDS；返回 (H,W,4) uint8。"""
    with Image.open(path) as im:
        return np.asarray(im.convert("RGBA"), np.uint8).copy()


def gather(mesh_path):
    root = read_meshfile(mesh_path)
    nodes = []
    for obj in root:
        for shape in obj:
            for m in shape.findall("mesh"):
                if "p" not in m.attrib:
                    continue
                mats = m.find("material")
                d = dict(
                    P=np.array(m.get("p"), np.float64).reshape(-1, 3),
                    N=np.array(m.get("n"), np.float64).reshape(-1, 3) if m.get("n") else None,
                    T=np.array(m.get("tri"), np.int64).reshape(-1, 3),
                    diff=(mats.get("diff")[0] if mats is not None and mats.get("diff") else None),
                )
                sk = m.find("skin")
                if sk is not None and sk.get("ix"):
                    d["ix"] = np.array(sk.get("ix"), np.int64).reshape(-1, 4)
                    d["w"] = np.array(sk.get("w"), np.float64).reshape(-1, 4)
                uv = m.get("u0")
                d["UV"] = np.array(uv, np.float64).reshape(-1, 2) if uv else None
                nodes.append(d)
    return nodes


def sample(tex, uv):
    """uv (N,2) 在 [0,1]；最近邻 + 环绕。tex (H,W,4)。"""
    H, W = tex.shape[0], tex.shape[1]
    x = np.clip((uv[:, 0] * W).astype(np.int64), 0, W - 1)
    y = np.clip((uv[:, 1] * H).astype(np.int64), 0, H - 1)
    return tex[y, x]


def render(nodes, outdir, W, H, view, bone_shade=False, bg=(24, 26, 32),
           zoom=1.0, focus_y=None, depth_le=False, cull=True):
    # 相机
    az, el = view
    ca, sa = math.cos(az), math.sin(az)
    ce, se = math.cos(el), math.sin(el)
    fwd = np.array([ca * ce, se, sa * ce])
    fwd /= np.linalg.norm(fwd)
    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(fwd, up0)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    # 收集所有顶点定尺度
    allP = np.concatenate([n["P"] for n in nodes], 0)
    c = allP.mean(0)
    if focus_y is not None:
        c = np.array([allP[:, 0].mean(), focus_y, allP[:, 2].mean()])
    r = np.linalg.norm(allP - c, axis=1).max()
    scale = min(W, H) / (2.0 * r * 1.05) * zoom

    img = np.zeros((H, W, 3), np.float64)
    # bg 给的是 0-255 整数；整张图最后会 *255，所以这里必须先归一到 0-1，
    # 否则会整数回绕（24*255 mod 256 = 232，浅米色底就是这么来的）。
    img[:] = np.array(bg, np.float64) / 255.0
    zbuf = np.full((H, W), 1e18)

    # 灯光跟随相机（否则背面视角或正面视角会全黑）
    light = -fwd + 0.45 * up + 0.30 * right
    light /= np.linalg.norm(light)

    for nd in nodes:
        tex = None
        if nd["diff"]:
            p = os.path.join(outdir, nd["diff"])
            if os.path.isfile(p):
                tex = load_dds(p)
        P = nd["P"]
        # 世界 -> 相机
        rel = P - c
        sx = rel @ right
        sy = rel @ up
        sz = rel @ fwd
        px = (W / 2 + sx * scale)
        py = (H / 2 - sy * scale)

        nrm = nd["N"] if nd["N"] is not None else np.zeros_like(P)
        if bone_shade and "ix" in nd:
            base = np.array([[0.35, 0.55, 0.9], [0.95, 0.6, 0.35], [0.45, 0.85, 0.5],
                             [0.85, 0.4, 0.75], [0.9, 0.85, 0.4], [0.4, 0.8, 0.85]])
            col = np.zeros((len(P), 3))
            for j in range(4):
                m = nd["ix"][:, j] >= 0
                col[m] += base[nd["ix"][m, j] % len(base)] * nd["w"][m, j:j + 1]
            col = np.clip(col, 0, 1)
        else:
            col = None

        T = nd["T"]
        for t in T:
            i0, i1, i2 = t
            x0, y0 = px[i0], py[i0]
            x1, y1 = px[i1], py[i1]
            x2, y2 = px[i2], py[i2]
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            if abs(area) < 1e-9:
                continue
            # 屏幕 y 向下，所以符号相反；保留正面（几何法线朝相机）
            # 注意：MMD 的脸/眼材质常标记为双面（draw_flag 0x01），
            # 用单面剔除会让眼球整层消失 —— 那是我方渲染器的局限，不是模型问题。
            if cull and area >= 0:
                continue
            z0, z1, z2 = sz[i0], sz[i1], sz[i2]
            minx = max(int(np.floor(min(x0, x1, x2))), 0)
            maxx = min(int(np.ceil(max(x0, x1, x2))), W - 1)
            miny = max(int(np.floor(min(y0, y1, y2))), 0)
            maxy = min(int(np.ceil(max(y0, y1, y2))), H - 1)
            if minx > maxx or miny > maxy:
                continue
            gx, gy = np.meshgrid(np.arange(minx, maxx + 1) + 0.5,
                                 np.arange(miny, maxy + 1) + 0.5)
            w0 = ((x1 - gx) * (y2 - gy) - (x2 - gx) * (y1 - gy)) / area
            w1 = ((x2 - gx) * (y0 - gy) - (x0 - gx) * (y2 - gy)) / area
            w2 = 1.0 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            z = w0 * z0 + w1 * z1 + w2 * z2
            sub_z = zbuf[miny:maxy + 1, minx:maxx + 1]
            # MMD 的叠层材质（脸/眼/袜/翼）深度完全重合，谁可见取决于深度测试规则：
            #   depth_le=False → 严格 '<'，先画的赢（等价 D3D LESS）
            #   depth_le=True  → '<='，后画的赢（等价 D3D LESS_EQUAL，HOI4 的实际默认）
            sel = inside & ((z <= sub_z) if depth_le else (z < sub_z))
            if not sel.any():
                continue
            yy, xx = np.nonzero(sel)
            zz = z[yy, xx]
            sub_z[yy, xx] = zz
            # 光照
            n = (w0[yy, xx, None] * nrm[i0] + w1[yy, xx, None] * nrm[i1]
                 + w2[yy, xx, None] * nrm[i2])
            ln = np.linalg.norm(n, axis=1, keepdims=True)
            n = n / np.maximum(ln, 1e-9)
            lam = np.clip(n @ light, 0, 1) * 0.75 + 0.32
            # 颜色
            if col is not None:
                base_c = (w0[yy, xx, None] * col[i0] + w1[yy, xx, None] * col[i1]
                          + w2[yy, xx, None] * col[i2])
            elif tex is not None and nd["UV"] is not None:
                uv = (w0[yy, xx, None] * nd["UV"][i0] + w1[yy, xx, None] * nd["UV"][i1]
                      + w2[yy, xx, None] * nd["UV"][i2])
                base_c = sample(tex, np.stack([uv[:, 0], uv[:, 1]], 1))[:, :3] / 255.0
            else:
                base_c = np.full((len(yy), 3), 0.7)
            img[miny + yy, minx + xx] = np.clip(base_c * lam[:, None], 0, 1)

    return (img * 255).astype(np.uint8)


# 角色朝 -Z（MMD 脚尖朝 -Z），所以"正面"= 相机在 -Z 朝 +Z 看
def fresh(path):
    """工作区禁止覆盖已存在文件，被占用就自动加序号。"""
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    i = 2
    while os.path.exists("%s_%d%s" % (stem, i, ext)):
        i += 1
    return "%s_%d%s" % (stem, i, ext)


VIEWS = {
    "front": (math.pi / 2, 0.10),
    "back": (-math.pi / 2, 0.10),
    "left": (math.pi, 0.10),
    "right": (0.0, 0.10),
    "q34": (math.pi / 2 - 0.7, 0.16),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh")
    ap.add_argument("--w", type=int, default=420)
    ap.add_argument("--h", type=int, default=820)
    ap.add_argument("--bone-shade", action="store_true")
    ap.add_argument("--depth-le", action="store_true",
                    help="用 <= 深度测试（模拟 D3D LESS_EQUAL / HOI4 默认），"
                         "重合叠层由后画的材质胜出")
    ap.add_argument("--no-cull", action="store_true",
                    help="关闭背面剔除（用于检查被单面剔除误杀的层，如 MMD 的双面眼球材质）")
    ap.add_argument("--views", default="front,q34,left")
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--focus-y", type=float, default=None)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    mesh = os.path.abspath(args.mesh)
    outdir = os.path.dirname(mesh)
    nodes = gather(mesh)
    tot_v = sum(len(n["P"]) for n in nodes)
    tot_t = sum(len(n["T"]) for n in nodes)
    print("mesh: %s  节点 %d  顶点 %d  三角 %d" % (mesh, len(nodes), tot_v, tot_t))

    imgs = []
    for name in args.views.split(","):
        if name not in VIEWS:
            continue
        a = render(nodes, outdir, args.w, args.h, VIEWS[name], args.bone_shade,
                   zoom=args.zoom, focus_y=args.focus_y, depth_le=args.depth_le,
                   cull=not args.no_cull)
        p = fresh(os.path.join(outdir, "preview_%s%s%s%s%s.png"
                               % (args.tag, name, "_bone" if args.bone_shade else "",
                                  "_le" if args.depth_le else "",
                                  "_nocull" if args.no_cull else "")))
        Image.fromarray(a).save(p)
        print("  -> %s" % p)
        imgs.append(a)

    if imgs:
        sheet = np.concatenate(imgs, axis=1)
        p = fresh(os.path.join(outdir, "preview_%ssheet%s%s%s.png"
                               % (args.tag, "_bone" if args.bone_shade else "",
                                  "_le" if args.depth_le else "",
                                  "_nocull" if args.no_cull else "")))
        Image.fromarray(sheet).save(p)
        print("  -> %s (%dx%d)" % (p, sheet.shape[1], sheet.shape[0]))


if __name__ == "__main__":
    main()

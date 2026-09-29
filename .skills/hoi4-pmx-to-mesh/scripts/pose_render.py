# -*- coding: utf-8 -*-
"""用真实 HOI4 动画给模型摆姿势并渲染 —— 离线验证骨骼绑定是否正确。

原理
  .anim 里每根骨存的是「相对父骨的完整局部变换」(t, q, s)，**不是 delta**：
      M_b = M_parent @ T(t_b) @ R(q_b) @ S(s_b)
  蒙皮矩阵   skin_b = M_b @ inv_bind_b     （inv_bind_b 就是 .mesh 骨架里的 tx）
  顶点       v' = Σ w_i · skin_{g_i} · v

  关键：旋转发生在**骨自己的原点**上。所以如果网格没对齐到骨架的 rest
  位置（腿的骨在 x=0.88 而腿的网格在 x=0.15），腿就会绕错误的圆心摆动。

用法
  python pose_render.py <mesh> <anim> [--frame N] [--outdir D] [--tag X]
                        [--views front,left,q34] [--w 480] [--h 720]
                        [--zoom 1.0] [--focus-y Y] [--bone-shade]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdx_data import read_meshfile  # noqa: E402
import render_preview as RP        # noqa: E402


def fresh(path):
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    i = 2
    while os.path.exists("%s_%d%s" % (stem, i, ext)):
        i += 1
    return "%s_%d%s" % (stem, i, ext)


# ------------------------------------------------------------------ 数学
def quat_mat3(q):
    """HOI4 的四元数顺序是 (x, y, z, w)。"""
    x, y, z, w = (float(v) for v in q)
    n = x * x + y * y + z * z + w * w
    if n < 1e-12:
        return np.eye(3)
    s = 2.0 / n
    return np.array([
        [1 - s * (y * y + z * z), s * (x * y - z * w),     s * (x * z + y * w)],
        [s * (x * y + z * w),     1 - s * (x * x + z * z), s * (y * z - x * w)],
        [s * (x * z - y * w),     s * (y * z + x * w),     1 - s * (x * x + y * y)],
    ], np.float64)


def m4(rot=None, trans=None, scale=None):
    M = np.eye(4)
    if rot is not None:
        M[:3, :3] = rot
    if scale is not None:
        M[:3, :3] = M[:3, :3] * np.asarray(scale, np.float64).reshape(1, -1)
    if trans is not None:
        M[:3, 3] = np.asarray(trans, np.float64)
    return M


def read_tx(tx):
    """tx = 列主序 3x4 的「逆绑定」矩阵 -> 4x4。
    退化情形（都要换掉，否则求逆会爆）：
      · Left_Hand_node 的值 ~1e12
      · Root_node_1 / Root_node_2 全 0（det=0）
    返回 (4x4, 是否退化)。"""
    a = np.asarray(tx, np.float64)
    cols = a.reshape(4, 3)
    R = cols[:3].T
    det = float(np.linalg.det(R))
    bad = (float(np.abs(a).max()) > 1e5) or (abs(det) < 1e-6)
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = cols[3]
    return M, bad


# ------------------------------------------------------------------ 读取
def load_mesh(path):
    root = read_meshfile(path)
    bones = []
    geoms = []
    for obj in root:
        for shape in obj:
            sk = shape.find("skeleton")
            if sk is not None:
                raw = []
                for b in sk:
                    M, bad = read_tx(b.get("tx"))
                    raw.append((b.tag, (b.get("pa") or [-1])[0], M, bad))
                # 修掉退化的 tx（Left_Hand_node 那类）：借用同前缀的下一根骨
                good = {nm: M for nm, _p, M, bad in raw if not bad}
                out = []
                for nm, pa, M, bad in raw:
                    if bad:
                        sub = good.get(nm + "_2")
                        if sub is None:
                            for k in sorted(good):
                                if k.startswith(nm):
                                    sub = good[k]
                                    break
                        M = np.eye(4) if sub is None else sub
                        print("  [修正] %s 的 tx 退化，改用替代矩阵" % nm)
                    out.append((nm, pa, M))
                bones = out
            for m in shape.findall("mesh"):
                if "p" not in m.attrib:
                    continue
                mats = m.find("material")
                g = dict(
                    P=np.array(m.get("p"), np.float64).reshape(-1, 3),
                    N=(np.array(m.get("n"), np.float64).reshape(-1, 3)
                       if m.get("n") else None),
                    T=np.array(m.get("tri"), np.int64).reshape(-1, 3),
                    diff=(mats.get("diff")[0]
                          if mats is not None and mats.get("diff") else None),
                )
                uv = m.get("u0")
                g["UV"] = np.array(uv, np.float64).reshape(-1, 2) if uv else None
                sk2 = m.find("skin")
                if sk2 is not None and sk2.get("ix"):
                    g["ix"] = np.array(sk2.get("ix"), np.int64).reshape(-1, 4)
                    g["w"] = np.array(sk2.get("w"), np.float64).reshape(-1, 4)
                geoms.append(g)
    return bones, geoms


def load_anim(path):
    root = read_meshfile(path)
    info = root.find("info")
    fps = float(info.get("fps")[0])
    frames = int(info.get("sa")[0])
    bones = []
    for b in info:
        sa = b.get("sa")[0]
        bones.append(dict(
            name=b.tag, sa=sa,
            t=np.array(b.get("t"), np.float64),
            q=np.array(b.get("q"), np.float64),
            s=np.array(b.get("s"), np.float64),
        ))
    sm = root.find("samples")
    samples = dict(t=np.array(sm.get("t"), np.float64),
                   q=np.array(sm.get("q"), np.float64),
                   s=np.array(sm.get("s"), np.float64))
    return fps, frames, bones, samples


def channel_slots(bones):
    """每个通道里，第 k 根「有这个通道的骨」占用第 k 段。"""
    off = {"t": 0, "q": 0, "s": 0}
    slot = {}
    for i, b in enumerate(bones):
        slot[i] = {}
        for c in "tqs":
            if c in b["sa"]:
                slot[i][c] = off[c]
                off[c] += 1
    return slot, off


def bone_locals_unused():
    return None


# ------------------------------------------------------------------ 主流程
def pose(bones, geoms, anim_path, frame):
    fps, frames, abones, samples = load_anim(anim_path)
    slot, counts = channel_slots(abones)
    n = len(bones)
    # 动画骨与骨架骨按名字对齐
    aidx = {}
    for i, b in enumerate(abones):
        aidx.setdefault(b["name"], i)

    # rest 局部：inv(bind_parent) @ bind
    binds = [np.linalg.inv(b[2]) for b in bones]
    rest_local = []
    for i, (nm, pa, invb) in enumerate(bones):
        if pa is None or pa < 0:
            rest_local.append(binds[i])
        else:
            rest_local.append(np.linalg.inv(binds[pa]) @ binds[i])

    frame = int(frame) % frames
    world = []
    for i, (nm, pa, invb) in enumerate(bones):
        ai = aidx.get(nm)
        if ai is None or abones[ai]["sa"] == "":
            L = rest_local[i]
        else:
            b = abones[ai]
            sl = slot[ai]
            # ★ 采样排列是「帧主序」：每一帧里把所有有该通道的骨依次排开。
            #   实测对照见 scripts/anim_convention.py —— 骨主序会让整个模型炸开。
            if "t" in sl:
                o = (frame * counts["t"] + sl["t"]) * 3
                t = samples["t"][o:o + 3]
            else:
                t = rest_local[i][:3, 3]
            if "q" in sl:
                o = (frame * counts["q"] + sl["q"]) * 4
                R = quat_mat3(samples["q"][o:o + 4])
            else:
                R = rest_local[i][:3, :3]
            if "s" in sl:
                o = frame * counts["s"] + sl["s"]
                sc = np.repeat(samples["s"][o:o + 1], 3)
            else:
                sc = np.ones(3)
            L = m4(R, t, sc)
        if pa is None or pa < 0:
            world.append(L)
        else:
            world.append(world[pa] @ L)

    skins = [world[i] @ bones[i][2] for i in range(n)]

    for g in geoms:
        if "ix" not in g:
            continue
        P = g["P"]
        N = g["N"]
        v = np.zeros_like(P)
        nn = np.zeros_like(P) if N is not None else None
        for k in range(4):
            gix = g["ix"][:, k]
            w = g["w"][:, k]
            good = (w > 1e-8) & (gix >= 0) & (gix < n)
            if not good.any():
                continue
            idx = np.where(good)[0]
            S = np.array([skins[gix[j]] for j in idx])
            vv = P[idx]
            v[idx] += w[idx, None] * np.einsum("nij,nj->ni", S[:, :3, :3], vv) \
                + w[idx, None] * S[:, :3, 3]
            if nn is not None:
                nn[idx] += w[idx, None] * np.einsum("nij,nj->ni", S[:, :3, :3], N[idx])
        g["P"] = v
        if nn is not None:
            ln = np.linalg.norm(nn, axis=1, keepdims=True)
            g["N"] = nn / np.maximum(ln, 1e-9)
    return fps, frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh")
    ap.add_argument("anim")
    ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--tag", default="pose")
    ap.add_argument("--views", default="front,left,q34")
    ap.add_argument("--w", type=int, default=460)
    ap.add_argument("--h", type=int, default=700)
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--focus-y", type=float, default=None)
    ap.add_argument("--depth-le", action="store_true")
    ap.add_argument("--no-cull", action="store_true")
    ap.add_argument("--bone-shade", action="store_true")
    args = ap.parse_args()

    outdir = args.outdir or os.path.dirname(os.path.abspath(args.mesh))
    bones, geoms = load_mesh(args.mesh)
    fps, frames = pose(bones, geoms, args.anim, args.frame)
    print("骨架 %d 根骨，mesh 节点 %d，anim fps=%.2f 帧数=%d，渲染第 %d 帧"
          % (len(bones), len(geoms), fps, frames, args.frame % frames))

    for view in args.views.split(","):
        img = RP.render(geoms, outdir, args.w, args.h, RP.VIEWS[view],
                        zoom=args.zoom, focus_y=args.focus_y,
                        depth_le=args.depth_le, cull=not args.no_cull,
                        bone_shade=args.bone_shade)
        # 多视角时并排；单视角时直接存
        p = fresh(os.path.join(outdir, "%s_%s.png" % (args.tag, view)))
        from PIL import Image
        Image.fromarray(img).save(p)
        print("  ->", p)


if __name__ == "__main__":
    main()

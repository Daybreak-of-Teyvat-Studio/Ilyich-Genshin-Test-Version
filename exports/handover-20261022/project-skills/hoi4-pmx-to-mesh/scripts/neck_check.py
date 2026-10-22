# -*- coding: utf-8 -*-
"""颈部诊断：按 y 分带统计顶点/骨骼的分布，定位「没脖子/脖子太长」。

用法: python neck_check.py <mesh> [mesh2 ...]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
import pdx_data  # noqa: E402


VERT, BONES, DOM = [], [], []          # 模块级暂存（load 填，main 用）


def load(path):
    root = pdx_data.read_meshfile(path)
    verts, bones = [], []
    dom = []
    for obj in root:
        for shape in obj:
            sk = shape.find("skeleton")
            if sk is not None:
                for b in sk:
                    bones.append((b.tag, b.get("ix"), b.get("pa")))
            for m in shape.findall("mesh"):
                # ⚠ p/n/ta/u0/tri 是 mesh 的「属性」，不是子节点
                if "p" not in m.attrib:
                    continue
                a = np.array(m.attrib["p"], np.float64).reshape(-1, 3)
                verts.append(a)
                sk2 = m.find("skin")
                if sk2 is not None and sk2.get("ix"):
                    ix = np.array(sk2.get("ix"), np.int64).reshape(-1, 4)
                    w = np.array(sk2.get("w"), np.float64).reshape(-1, 4)
                    if len(ix) == len(a):
                        dom.append(ix[np.arange(len(ix)), np.argmax(w, axis=1)])
                    else:
                        dom.append(np.full(len(a), -1, np.int64))
                else:
                    dom.append(np.full(len(a), -1, np.int64))
    return np.vstack(verts), bones, (np.concatenate(dom) if dom else None)


def main():
    out = []
    meshes = sys.argv[1:]
    for path in meshes:
        V, bones, dom = load(path)
        tag = os.path.basename(os.path.dirname(os.path.abspath(path)))
        y = V[:, 1]
        out.append("=" * 78)
        out.append("★ %s   顶点 %d    Y [%.3f, %.3f]" % (tag, len(V), y.min(), y.max()))
        # 骨架里 head / back_mid / 肩 的位置
        for nm, ix, pa in bones:
            if nm in ("head", "back_mid", "Hip", "LeftShoulder", "LeftArm"):
                out.append("   骨骼 %-14s ix=%-3s pa=%-3s" % (nm, ix, pa))

        # 关键：上体「横截面宽度」沿 y 的剖面。脖子细、头宽、肩很宽。
        out.append("")
        out.append("   y 分带剖面（带内顶点数 / x 跨度 / x 中位绝对偏移）")
        out.append("    %-16s %8s %9s %9s" % ("y 区间", "顶点数", "x跨度", "|x|中位"))
        bands = np.arange(3.6, 8.01, 0.2)
        for lo, hi in zip(bands[:-1], bands[1:]):
            m = (y >= lo) & (y < hi)
            n = int(m.sum())
            if n == 0:
                out.append("    %-16s %8d %9s %9s" % ("%.1f-%.1f" % (lo, hi), 0, "-", "-"))
                continue
            xs = np.abs(V[m, 0])
            out.append("    %-16s %8d %9.3f %9.3f"
                       % ("%.1f-%.1f" % (lo, hi), n, V[m, 0].max() - V[m, 0].min(),
                          np.median(xs)))
        # 空带高亮
        empt = [("%.1f-%.1f" % (lo, hi)) for lo, hi in zip(bands[:-1], bands[1:])
                if ((y >= lo) & (y < hi)).sum() == 0]
        if empt:
            out.append("   ★★ 完全空白的 y 带：%s" % ", ".join(empt))
        # ★ 中轴半径剖面：只统计靠近中线的顶点（|x|<0.9），把翅膀/手臂/长发排除在外。
        #   「脖子」的几何特征 = 中轴最细的那一段。用它比 y 分带宽度可靠得多。
        out.append("")
        out.append("  中轴半径剖面（|x|<0.9 的顶点；半宽 = |x| 的 P90）")
        out.append("    %-16s %8s %9s %9s" % ("y 区间", "顶点数", "半宽", "|x|中位"))
        for lo, hi in zip(bands[:-1], bands[1:]):
            m = (y >= lo) & (y < hi) & (np.abs(V[:, 0]) < 0.9)
            if not m.sum():
                out.append("    %-16s %8d %9s %9s" % ("%.1f-%.1f" % (lo, hi), 0, "-", "-"))
                continue
            ax = np.abs(V[m, 0])
            out.append("    %-16s %8d %9.3f %9.3f"
                       % ("%.1f-%.1f" % (lo, hi), int(m.sum()),
                          np.quantile(ax, 0.9), np.median(ax)))
        # 找中轴最细处
        rows = []
        for lo, hi in zip(bands[:-1], bands[1:]):
            m = (y >= lo) & (y < hi) & (np.abs(V[:, 0]) < 0.9)
            if m.sum() > 40:
                rows.append((np.quantile(np.abs(V[m, 0]), 0.9), lo, hi, int(m.sum())))
        if rows:
            rows.sort()
            out.append("   ★ 中轴最细的三段（脖子候选）：%s"
                       % "  ".join("%.1f-%.1f(半宽%.3f,n=%d)" % (a, b, w, n)
                                   for w, a, b, n in rows[:3]))
        out.append("")

        # 按「主导骨」分组：头部骨到底管着哪一段几何？(和原版 PRC 比就知道对没对)
        if dom is not None:
            i2n = {}
            for nm, ix, pa in bones:
                i2n[int(np.asarray(ix).ravel()[0])] = nm
            out.append("  按主导骨（权重最大的骨）分组：")
            out.append("    %-16s %8s  %-24s %s" % ("骨", "顶点数", "y 范围", "质心"))
            for tgt in ("head", "back_mid", "Hip", "LeftShoulder", "LeftArm",
                        "LeftUpLeg", "LeftLeg", "LeftFoot"):
                i = next((k for k, v in i2n.items() if v == tgt), None)
                if i is None:
                    continue
                sel = dom == i
                if not sel.sum():
                    out.append("    %-16s %8d" % (tgt, 0))
                    continue
                c = V[sel].mean(0)
                out.append("    %-16s %8d  [%6.3f,%6.3f]        (%6.3f,%6.3f,%6.3f)"
                           % (tgt, int(sel.sum()), V[sel, 1].min(), V[sel, 1].max(),
                              c[0], c[1], c[2]))
        out.append("")

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_neck_check")
    p = base + ".txt"
    n = 2
    while True:
        try:
            fh = open(p, "w", encoding="utf-8")
            break
        except PermissionError:
            p = "%s_%d.txt" % (base, n)
            n += 1
    fh.write("\n".join(out))
    fh.close()
    print("\n".join(out))
    print("\n-> %s" % p)


if __name__ == "__main__":
    main()

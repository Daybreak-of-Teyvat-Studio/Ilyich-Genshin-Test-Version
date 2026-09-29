#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""HOI4 建筑悬空修复：按 heightmap 重算 map/buildings.txt 的第 4 列（绝对高程）。

用法
----
    # 1) 只诊断，不动文件（默认）
    python fix_buildings_height.py --map "<...>/Daybreak of Teyvat Gamma Version/map"

    # 2) 出力到新文件（推荐：工作区内新建永远允许）
    python fix_buildings_height.py --map "<...>/map" --out "<...>/.workbuddy/buildings_fixed.txt"

    # 3) 改阈值 / 换高度图
    python fix_buildings_height.py --map "<...>/map" --tol 0.02 --heightmap heightmap.bmp

原理
----
map/buildings.txt 每行格式：  province;type;x;y;z;rotation;?
**第 4 列 y 是引擎直接使用的绝对高程**，不是你随手能改的偏移量。
它由 heightmap 采样而来：

        y = A * h + B            A = 0.09786518    B = 0.259962

采样位置：**row = z, col = x（不翻转！）**，用双线性取 h。
（heightmap 一改，所有建筑的 y 立刻过期 —— 这就是"建筑悬空/入地"的唯一根因。）

判据：非浮港建筑用该映射时 100.00% 落在陆地(h>=96)；
      用 row = H-1-z 翻转映射只有 32.74%（这就是错误记忆的由来）。
"""
import argparse
import os
import struct
import sys

import numpy as np

A = 0.09786518
B = 0.259962
SEA_LEVEL = 94          # 高度图海平面；h 低于此值按此值钳（防止码头/浮港掉到海面下）
SKIP_TYPES = {"floating_harbor"}   # 本来就该在水里的类型，不改


def read_heightmap(path, flip=False):
    """读 8 位索引 BMP 的像素矩阵。返回 (h, W, H)。

    ⚠️ **flip 默认为 False，即按 BMP 存储行序直接 reshape，不做翻转。**
    这一点反直觉（BMP 通常是 bottom-up），但实测是对的：
    `buildings.txt` 的 `z` 直接对应存储行序，翻转后非浮港建筑的陆地命中率
    会从 100.00% 掉到 32.74%，残差从 0.0032 恶化到 6.5。
    脚本内置自检：若残差 mean|r| > 1.0 会提示重新考虑 flip。
    """
    raw = open(path, "rb").read()
    off = struct.unpack_from("<I", raw, 10)[0]
    W = struct.unpack_from("<i", raw, 18)[0]
    H = struct.unpack_from("<i", raw, 22)[0]
    if H < 0:                       # 负 biHeight = top-down BMP
        H = -H
    bpp = struct.unpack_from("<H", raw, 28)[0]          # 注意：bpp 在偏移 28，不是 26
    if bpp != 8:
        print(f"[warn] heightmap 位深 = {bpp}，非 8 位索引；仍按单字节解析，请自行确认", file=sys.stderr)
    # 像素体后常有 2 个多余字节，按 off + W*H 截断
    buf = np.frombuffer(raw, dtype=np.uint8, offset=off)
    if buf.size < W * H:
        raise ValueError(f"heightmap 字节不足：{buf.size} < {W*H}")
    arr = buf[: W * H].reshape(H, W)
    if flip:
        arr = arr[::-1]
    return arr, W, H


def bilinear(hm, x, z):
    """在 (col=x, row=z) 处双线性采样。整数采样会带来约 0.03 的系统偏差。"""
    H, W = hm.shape
    if not (0 <= x < W - 1 and 0 <= z < H - 1):
        c = min(max(int(round(x)), 0), W - 1)
        r = min(max(int(round(z)), 0), H - 1)
        return float(hm[r, c]), (r, c)
    c0, r0 = int(x), int(z)
    dc, dr = x - c0, z - r0
    v = (hm[r0, c0] * (1 - dc) + hm[r0, c0 + 1] * dc) * (1 - dr) + \
        (hm[r0 + 1, c0] * (1 - dc) + hm[r0 + 1, c0 + 1] * dc) * dr
    return float(v), (r0, c0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True, help="MOD 的 map 目录")
    ap.add_argument("--heightmap", default="heightmap.bmp")
    ap.add_argument("--buildings", default="buildings.txt")
    ap.add_argument("--out", default=None, help="不指定则只诊断")
    ap.add_argument("--tol", type=float, default=0.005, help="残差绝对值小于此值的行保持原样")
    ap.add_argument("--flip", action="store_true", help="高度图按 BMP bottom-up 翻转（默认不翻转）")
    ap.add_argument("--report", default=None, help="报告落盘路径（可选）")
    args = ap.parse_args()

    mapdir = args.map
    hmpath = os.path.join(mapdir, args.heightmap)
    hm, W, H = read_heightmap(hmpath, flip=args.flip)

    # ---- 行序自检：把两种 flip 各算一遍，选残差小的那个 ----
    alt = read_heightmap(hmpath, flip=not args.flip)[0]

    def _quick(hmx):
        """抽样 4000 条算 |残差| 的**中位数**。

        用中位数而不是均值：表里常常混着一批从未初始化的行（y 全等于 9.50），
        它们会把均值抬高，让行序自检做出错误结论。中位数对这些异常行免疫。
        """
        rs = []
        for ln in open(os.path.join(mapdir, args.buildings), encoding="utf-8", errors="replace"):
            f = ln.split(";")
            if len(f) < 6 or f[1] in SKIP_TYPES:
                continue
            try:
                x, y, z = float(f[2]), float(f[3]), float(f[4])
            except ValueError:
                continue
            h, _ = bilinear(hmx, x, z)
            rs.append(abs(y - (A * h + B)))
            if len(rs) >= 4000:
                break
        return float(np.median(rs)) if rs else 9e9

    e_now, e_alt = _quick(hm), _quick(alt)
    if e_alt < e_now * 0.5:   # 另一种行序明显更贴合 -> 自动切换
        hm = alt
        flip_note = f"行序自检：自动切到 flip={not args.flip}（|r|中位 {e_alt:.4f} 优于 {e_now:.4f}）"
    else:
        flip_note = f"行序自检通过：flip={args.flip}，抽样 |r| 中位={e_now:.4f}"
    bpath = os.path.join(mapdir, args.buildings)
    raw_text = open(bpath, encoding="utf-8", errors="replace").read()
    # 保留原始换行风格
    eol = "\r\n" if "\r\n" in raw_text else "\n"
    lines = raw_text.split(eol)

    out_lines = []
    stats = {"total": 0, "skip_float": 0, "unchanged": 0, "fixed": 0, "oob": 0}
    res_old, res_new = [], []
    fixed_rows = []

    for ln in lines:
        f = ln.split(";")
        if len(f) < 6:
            out_lines.append(ln)
            continue
        try:
            btype = f[1]
            x, y, z = float(f[2]), float(f[3]), float(f[4])
        except ValueError:
            out_lines.append(ln)
            continue

        stats["total"] += 1
        if btype in SKIP_TYPES:
            stats["skip_float"] += 1
            out_lines.append(ln)
            continue

        h, (r, c) = bilinear(hm, x, z)
        res_old.append(y - (A * h + B))
        if not (0 <= r < H and 0 <= c < W):
            stats["oob"] += 1
            out_lines.append(ln)
            continue

        hc = max(h, SEA_LEVEL)                 # 钳到海平面，避免码头掉到水面下
        y_new = A * hc + B
        res_new.append(y - y_new)

        if abs(y - y_new) <= args.tol:
            stats["unchanged"] += 1
            out_lines.append(ln)
        else:
            stats["fixed"] += 1
            f[3] = f"{y_new:.2f}"
            newln = ";".join(f)
            out_lines.append(newln)
            fixed_rows.append((f[0], btype, x, z, y, y_new, h))

    res_old = np.array(res_old) if res_old else np.zeros(1)
    res_new = np.array(res_new) if res_new else np.zeros(1)

    rep = []
    P = rep.append
    P("=" * 72)
    P("HOI4 建筑悬空诊断 / 修复报告")
    P("=" * 72)
    P(f"map 目录   : {mapdir}")
    P(f"高度图     : {args.heightmap}  ({W}x{H}, 8bpp)")
    P(f"映射       : row = z, col = x  (不翻转)")
    P(f"             {flip_note}")
    P(f"公式       : y = {A} * h + {B}   (h 下限钳到 {SEA_LEVEL})")
    P("-" * 72)
    P(f"记录总数            : {stats['total']:,}")
    P(f"浮动港口(跳过)      : {stats['skip_float']:,}")
    P(f"越界(保留原值)      : {stats['oob']:,}")
    P(f"残差<= {args.tol} (保留)  : {stats['unchanged']:,}")
    P(f"需要修正            : {stats['fixed']:,}")
    P("-" * 72)
    P("[修复前] 残差 y-(A*h+B)（不含浮港/越界）")
    P(f"   样本 {res_old.size:,}   mean={res_old.mean():+.4f}  mean|r|={np.abs(res_old).mean():.4f}"
      f"  median|r|={np.median(np.abs(res_old)):.4f}  max|r|={np.abs(res_old).max():.4f}")
    for th in (0.01, 0.1, 0.5, 1.0, 3.0, 5.0):
        P(f"   |r|>{th:<5}: {int((np.abs(res_old) > th).sum()):,}")
    n_sea = sum(1 for fr in fixed_rows if abs(fr[4] - 9.50) < 0.02)
    P(f"   待修行中 y 仍贴着海平面(|y-9.50|<0.02) 的: {n_sea}  (nudge 漏掉的典型症状)")
    P("")
    if stats["fixed"]:
        P("[修复后] 预期残差（对已改行）")
        P(f"   样本 {res_new.size:,}   mean|r|={np.abs(res_new).mean():.4f}  max|r|={np.abs(res_new).max():.4f}")
        P("")
        P("[位移最大的 30 条]")
        P(f"   {'prov':<7}{'type':<30}{'x':>10}{'z':>10}{'y_old':>9}{'y_new':>9}{'dY':>9}{'h':>7}")
        for fr in sorted(fixed_rows, key=lambda t: -abs(t[5] - t[4]))[:30]:
            P(f"   {fr[0]:<7}{fr[1]:<30}{fr[2]:>10.2f}{fr[3]:>10.2f}"
              f"{fr[4]:>9.2f}{fr[5]:>9.2f}{fr[5]-fr[4]:>+9.2f}{fr[6]:>7.1f}")
    P("=" * 72)

    text = "\n".join(rep)
    print(text)
    if args.report:
        open(args.report, "w", encoding="utf-8").write(text)
        print(f"\n[report] -> {args.report}")

    if args.out:
        blob = eol.join(out_lines)
        open(args.out, "w", encoding="utf-8", newline="").write(blob)
        print(f"[out]    -> {args.out}  ({len(blob)} bytes)")
    else:
        print("\n[!] 未指定 --out，仅诊断。确认无误后加 --out 出力。")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 本模块方法由 绿豆糕 制作
"""HOI4 建筑高程重算落地（CRLF 保持版）。

按 heightmap 重算 map/buildings.txt 第 4 列绝对高程，**字节级保持 CRLF 行尾**，
只允许第 4 列变化。修 fix_buildings_height.py 的 universal-newlines 陷阱
（默认 open() 会把 \\r\\n 静默转 \\n，导致换行检测误判、输出变纯 LF）。

用法
----
    # 1) 只诊断，不动文件
    python fix_height_crlf.py --map "<mod>/map"

    # 2) 出力到新文件（确认后自行落回）
    python fix_height_crlf.py --map "<mod>/map" --out buildings_fixed.txt

规则与 fix_buildings_height.py 相同：y = 0.09786518*h + 0.259962，
双线性采样、行序自检（中位数）、floating_harbor 跳过、海上钳 h>=94、容差 0.005。
"""
import argparse
import collections
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_buildings_height import read_heightmap, bilinear, A, B, SEA_LEVEL, SKIP_TYPES  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True, help="MOD 的 map 目录")
    ap.add_argument("--buildings", default="buildings.txt")
    ap.add_argument("--out", default=None, help="不指定则只诊断")
    ap.add_argument("--tol", type=float, default=0.005)
    args = ap.parse_args()

    BP = os.path.join(args.map, args.buildings)
    hm, W, H = read_heightmap(os.path.join(args.map, 'heightmap.bmp'), flip=False)

    raw = open(BP, 'rb').read()
    assert b'\r\n' in raw, '原文件不是 CRLF（本脚本只处理纯 CRLF；请先确认文件行尾）'
    lines = raw.decode('utf-8').split('\r\n')
    print(f'读入 {len(lines)} 行（纯 CRLF：{raw.count(bytes([13, 10]))} / LF {raw.count(bytes([10]))}）')

    alt = read_heightmap(os.path.join(args.map, 'heightmap.bmp'), flip=True)[0]

    def quick_median(hmx):
        rs = []
        for ln in lines:
            f = ln.split(';')
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

    m0, m1 = quick_median(hm), quick_median(alt)
    if m1 < m0 * 0.5:
        hm = alt
        print(f'行序自检：切换到翻转（|r|中位 {m1:.4f} 优于 {m0:.4f}）')
    else:
        print(f'行序自检：不翻转（|r|中位 {m0:.4f}）')

    out, st = [], {'total': 0, 'skip': 0, 'keep': 0, 'fix': 0}
    for ln in lines:
        f = ln.split(';')
        if len(f) < 6:
            out.append(ln)
            continue
        try:
            btype, x, y, z = f[1], float(f[2]), float(f[3]), float(f[4])
        except ValueError:
            out.append(ln)
            continue
        st['total'] += 1
        if btype in SKIP_TYPES:
            st['skip'] += 1
            out.append(ln)
            continue
        h, (r, c) = bilinear(hm, x, z)
        if not (0 <= r < H and 0 <= c < W):
            out.append(ln)
            continue
        y_new = A * max(h, SEA_LEVEL) + B
        if abs(y - y_new) <= args.tol:
            st['keep'] += 1
        else:
            st['fix'] += 1
            f[3] = f'{y_new:.2f}'
            ln = ';'.join(f)
        out.append(ln)

    blob = '\r\n'.join(out)
    print(f"统计: 总 {st['total']} / 浮港跳过 {st['skip']} / 保留 {st['keep']} / 修正 {st['fix']}")

    # 逐行核对：只该第 4 列变化
    old_lines = raw.decode('utf-8').split('\r\n')
    cc = collections.Counter()
    for a, b in zip(old_lines, blob.split('\r\n')):
        if a == b:
            continue
        fa, fb = a.split(';'), b.split(';')
        ch = [j for j in range(min(len(fa), len(fb))) if fa[j] != fb[j]]
        cc[tuple(ch)] += 1
    print(f'逐行差异形态（字段下标）: {dict(cc)}')
    non_y = {k: v for k, v in cc.items() if k != (3,)}
    if non_y:
        print(f'!! 有 {sum(non_y.values())} 行改动了第 4 列以外的字段，禁止落盘！')

    if args.out:
        open(args.out, 'w', encoding='utf-8', newline='').write(blob)
        nb = open(args.out, 'rb').read()
        print(f'出力 {len(nb)} 字节（原 {len(raw)}，差 {len(nb)-len(raw):+d}）；'
              f'CRLF {nb.count(bytes([13,10]))} / LF {nb.count(bytes([10]))} / '
              f'BOM {nb[:3] == bytes([239, 187, 191])}')
        print(f'-> {args.out}')
    else:
        print('[!] 未指定 --out，仅诊断。')


if __name__ == "__main__":
    main()

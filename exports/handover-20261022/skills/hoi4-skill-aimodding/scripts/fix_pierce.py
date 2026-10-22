#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 本模块方法由 绿豆糕 制作
"""HOI4 建筑防穿模抬升：陡坡上被山体埋住的建筑基座抬到邻域 90 分位地面。

用法
----
    python fix_pierce.py --map "<mod>/map" [--backup-dir <目录>]

规则（v4，实测校准）：
  · naval 类（dockyard/naval_*/coastal_bunker）与 floating_harbor **永不抬**——它们就该贴水
  · 中心 h<96（水面）不动
  · 7x7 邻域海洋像素（h<90）占比 >25%：悬崖/海岸建筑，抬高会悬空 → 跳过
  · 其余：邻域 90 分位高度的 y 高于当前 y 超过 1.0 → 抬到 90 分位
    （90 分位而非 max：留 10% 余量防悬空；"邻域大部分地面高于基座"才是真嵌进坡里）
  · 字节级保持 CRLF，只改第 4 列

验收信号：抬升占比应在 10~20% 量级（全图过半 = 规则错了）；
抬升量长尾（+1 最多）；naval/海岸类零改动。
"""
import argparse
import collections
import datetime
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_buildings_height import read_heightmap, bilinear, A, B, SKIP_TYPES  # noqa: E402

RAD, SEA_FRAC, TH = 3, 0.25, 1.0
NAVAL = {'dockyard', 'naval_base_spawn', 'naval_supply_hub', 'naval_headquarters',
         'coastal_bunker', 'floating_harbor'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True, help="MOD 的 map 目录")
    ap.add_argument("--buildings", default="buildings.txt")
    ap.add_argument("--tol", type=float, default=1.0, help="邻域 90 分位高出多少才抬")
    ap.add_argument("--backup-dir", default=None, help="备份目录（默认 <map>/../.backups/）")
    args = ap.parse_args()

    BP = os.path.join(args.map, args.buildings)
    hm, W, H = read_heightmap(os.path.join(args.map, 'heightmap.bmp'), flip=False)
    raw = open(BP, 'rb').read()
    assert raw.count(b'\r\n') == raw.count(b'\n') and raw.count(b'\n'), '本脚本只处理纯 CRLF 文件'
    lines = raw.decode('utf-8').split('\r\n')

    # 滑动窗口 90 分位与海占比（7x7）
    pad = np.pad(hm, RAD, mode='edge')
    win = np.lib.stride_tricks.sliding_window_view(pad, (2 * RAD + 1, 2 * RAD + 1))
    fp90 = np.percentile(win, 90, axis=(-1, -2)).astype(np.int32)
    sea_frac = (win < 90).mean(axis=(-1, -2))

    out, st = [], collections.Counter()
    samples = []
    for ln in lines:
        f = ln.split(';')
        if len(f) != 7:
            out.append(ln)
            continue
        try:
            btype, x, y, z = f[1], float(f[2]), float(f[3]), float(f[4])
        except ValueError:
            out.append(ln)
            continue
        st['total'] += 1
        if btype in SKIP_TYPES or btype in NAVAL:
            st['naval'] += 1
            out.append(ln)
            continue
        h_c, _ = bilinear(hm, x, z)
        if h_c < 96:
            st['sea'] += 1
            out.append(ln)
            continue
        r0, c0 = int(round(z)) % H, int(round(x)) % W
        if sea_frac[r0, c0] > SEA_FRAC:
            st['coast'] += 1
            out.append(ln)
            continue
        y_fp = A * fp90[r0, c0] + B
        if y_fp - y > args.tol:
            f[3] = f'{max(y, y_fp):.2f}'
            st['lift'] += 1
            samples.append((y_fp - y, btype, x, z, y))
        else:
            st['keep'] += 1
        out.append(ln)

    blob = '\r\n'.join(out)
    bdir = args.backup_dir or os.path.join(os.path.dirname(args.map.rstrip('/\\')),
                                           '.backups',
                                           'buildings_lift_' +
                                           datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(bdir, exist_ok=True)
    shutil.copy2(BP, os.path.join(bdir, os.path.basename(BP)))
    open(BP, 'w', encoding='utf-8', newline='').write(blob)
    nb = open(BP, 'rb').read()
    print(f"统计: 总 {st['total']} / naval浮港 {st['naval']} / 水面 {st['sea']} / "
          f"海岸跳过 {st['coast']} / 保持 {st['keep']} / 抬升 {st['lift']}")
    print(f'字节 {len(raw)} -> {len(nb)}（{len(nb)-len(raw):+d}）；'
          f'CRLF {nb.count(bytes([13,10]))}；BOM {nb[:3] == bytes([239,187,191])}')
    dd = collections.Counter()
    for d, *_ in samples:
        dd[min(6, int(d))] += 1
    print('抬升量分布（世界单位）:', dict(sorted(dd.items())))
    print(f'备份: {bdir}')


if __name__ == "__main__":
    main()

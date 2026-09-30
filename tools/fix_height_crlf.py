# -*- coding: utf-8 -*-
"""
按 fix_buildings_height.py 的公式重算 y，但字节级保持 CRLF 行尾。
复用其 read_heightmap / bilinear / 常数；主循环自己控制换行。
"""
import os, sys, shutil, datetime
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version')
from fix_buildings_height import read_heightmap, bilinear, A, B, SEA_LEVEL, SKIP_TYPES

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
BP = os.path.join(MAP, 'buildings.txt')
OUT = os.path.join(ROOT, '.backups', 'buildings_fixed_crlf.txt')
TOL = 0.005

hm, W, H = read_heightmap(os.path.join(MAP, 'heightmap.bmp'), flip=False)
alt = read_heightmap(os.path.join(MAP, 'heightmap.bmp'), flip=True)[0]

raw = open(BP, 'rb').read()
assert b'\r\n' in raw, '原文件不是 CRLF'
text = raw.decode('utf-8')
lines = text.split('\r\n')
print(f'读入 {len(lines)} 行（纯 CRLF：{raw.count(bytes([13,10]))} / LF {raw.count(bytes([10]))}）')


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
    return float(np.median(rs))


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
    if abs(y - y_new) <= TOL:
        st['keep'] += 1
    else:
        st['fix'] += 1
        f[3] = f'{y_new:.2f}'
        ln = ';'.join(f)
    out.append(ln)

blob = '\r\n'.join(out)
open(OUT, 'w', encoding='utf-8', newline='').write(blob)
nb = open(OUT, 'rb').read()
print(f"统计: 总 {st['total']} / 浮港跳过 {st['skip']} / 保留 {st['keep']} / 修正 {st['fix']}")
print(f'出力 {len(nb)} 字节（原 {len(raw)}，差 {len(nb)-len(raw):+d}）')
print(f'CRLF {nb.count(bytes([13,10]))} / LF {nb.count(bytes([10]))} / BOM {nb[:3]==bytes([239,187,191])}')
# 逐行核对：只该第 4 列变化
o2 = text.split('\r\n')
n2 = blob.split('\r\n')
import collections
cc = collections.Counter()
for a, b in zip(o2, n2):
    if a == b:
        continue
    fa, fb = a.split(';'), b.split(';')
    ch = [j for j in range(min(len(fa), len(fb))) if fa[j] != fb[j]]
    cc[tuple(ch)] += 1
print(f'逐行差异形态: {dict(cc)}')

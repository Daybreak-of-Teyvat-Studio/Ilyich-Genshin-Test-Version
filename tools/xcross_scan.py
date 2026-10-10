# -*- coding: utf-8 -*-
"""xcross_scan.py —— 全图扫 X 交叉（a==d,b==c,a!=b），报告位置与省/kind"""
import os, sys, time, struct

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

gk, colors = {}, {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            pid = int(c[0])
        except ValueError:
            continue
        gk[pid] = c[4]
        colors[(int(c[1]), int(c[2]), int(c[3]))] = pid

p_bmp = os.path.join(G, 'map', 'provinces.bmp')
mt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p_bmp)))
print(f'provinces.bmp mtime: {mt}')

raw = open(p_bmp, 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
W, H = struct.unpack('<ii', raw[18:26])
RB = W * 3
print(f'{W}x{H} off={off}')

# 预解出每像素省 id（用 bytes 索引加速）
t0 = time.time()
# 用字节三元组 → id 的字典，逐像素查（纯 python 8.4M*? 偏慢但可接受，~2-4 分钟）
def pixid(i):
    return colors.get((raw[i + 2], raw[i + 1], raw[i]))

found = []
for z in range(H - 1):
    base = off + z * RB
    nbase = base + RB
    # 同一行做滑动：cache 上一轮 x 的四个点
    for x in range(W - 1):
        i = base + x * 3
        j = i + 3
        a = pixid(i)
        b = pixid(j)
        c = pixid(nbase + x * 3)
        d = pixid(nbase + x * 3 + 3)
        if a is not None and a == d and b is not None and b == c and a != b:
            found.append((x, z, a, b))
print(f'扫描完毕 {time.time()-t0:.1f}s，找到 {len(found)} 处 X 交叉')
# 分类统计
from collections import Counter
cat = Counter()
for x, z, a, b in found:
    cat[(gk.get(a), gk.get(b))] += 1
print('按 kind 组合:', dict(cat))
for x, z, a, b in found[:40]:
    print(f'  ({x},{z}) {a}({gk.get(a)}) {b}({gk.get(b)}) 图案 {a} {b}/{b} {a}   距(4095,480)={abs(x-4095)+abs(z-480)}')

# -*- coding: utf-8 -*-
"""nudge「地图定义文件存在错误」排查：
   ① provinces.bmp 颜色 vs definition.csv 定义 双向差集
   ② islands.txt / adjacencies.csv 等缺失检查
   ③ 与原版对比这些文件的存在性
"""
import os, re, sys, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
VAN = r'F:\Steam\steamapps\common\Hearts of Iron IV'

# definition.csv 定义的 (R,G,B) 与 id
def_rgb, def_id = {}, {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.rstrip('\r\n').split(';')
    if len(a) >= 8 and a[0].strip().isdigit():
        pid = int(a[0])
        rgb = (int(a[1]), int(a[2]), int(a[3]))
        def_rgb[rgb] = pid
        def_id[pid] = rgb

# provinces.bmp 实际颜色
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB'))
flat = arr.reshape(-1, 3)
colors = collections.Counter(map(tuple, flat.tolist()))
print(f'provinces.bmp 唯一颜色 {len(colors)} 个；definition.csv 定义 {len(def_rgb)} 个')

bmp_only = {c: n for c, n in colors.items() if c not in def_rgb}
def_only = [c for c in def_rgb if c not in colors]
print(f'\n① bmp 有、definition 没有: {len(bmp_only)} 个')
for c, n in sorted(bmp_only.items(), key=lambda x: -x[1])[:10]:
    print(f'     RGB {c}  像素 {n}')
print(f'① definition 有、bmp 没有: {len(def_only)} 个')
for c in def_only[:10]:
    print(f'     RGB {c}  = 省 {def_rgb[c]}')

# 同色多 id / 同 id 多色（definition 内部）
rgb_dup = [c for c, n in collections.Counter(
    (int(l.split(";")[1]), int(l.split(";")[2]), int(l.split(";")[3]))
    for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace')
    if len(l.split(';')) >= 8 and l.split(';')[0].strip().isdigit()).items() if n > 1]
print(f'② definition 内部重复 RGB: {len(rgb_dup)} {rgb_dup[:5]}')

# ③ 文件存在性对比
print('\n③ map/ 关键文件对比（mod vs 原版）:')
for f in ('definition.csv', 'provinces.bmp', 'terrain.bmp', 'heightmap.bmp', 'rivers.bmp',
          'adjacencies.csv', 'islands.txt', 'cities.txt', 'buildings.txt', 'positions.txt',
          'supply_nodes.txt', 'victory_points.txt', 'weatherpositions.txt', 'ambient_object.txt'):
    a = os.path.exists(os.path.join(G, 'map', f))
    b = os.path.exists(os.path.join(VAN, 'map', f))
    mark = '✓✓' if (a and b) else ('仅mod' if a else ('仅原版 ⚠' if b else '都无'))
    print(f'  {f:22s} mod={a}  原版={b}   {mark}')

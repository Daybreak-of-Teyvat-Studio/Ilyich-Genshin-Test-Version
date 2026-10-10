# -*- coding: utf-8 -*-
"""coastal_audit.py —— 沿海标记审计：definition.csv coastal(第6列) vs 地图实际邻海
输出：假沿海（标 true 但不邻海）与漏标（标 false 但邻海）清单 + 所属州"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

kind, coastal, rgb2id = {}, {}, {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.strip().split(';')
    if len(a) > 6 and a[0].strip().isdigit() and int(a[0]) > 0:
        pid = int(a[0])
        kind[pid] = a[4]
        coastal[pid] = (a[5].strip().lower() == 'true')
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = pid

arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
u, inv = np.unique(key, return_inverse=True)
pl = np.zeros(len(u), np.int32)
for i, k in enumerate(u):
    k = int(k)
    pl[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = pl[inv].reshape(H, W)

# 水体掩码（kind == sea）
sea_ids = np.array([p for p, k in kind.items() if k == 'sea'], dtype=np.int32)
lut = np.zeros(20001, bool)
lut[np.clip(sea_ids, 0, 20000)] = True
water = lut[np.clip(prov, 0, 20000)]

# 8 邻域：陆像素邻接水体
adj = np.zeros((H, W), bool)
for dy in (-1, 0, 1):
    for dx in (-1, 0, 1):
        if dy == 0 and dx == 0:
            continue
        sh = np.zeros((H, W), bool)
        ys0, ys1 = max(0, dy), min(H, H + dy)
        xs0, xs1 = max(0, dx), min(W, W + dx)
        sh[ys0:ys1, xs0:xs1] = water[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        adj |= sh
land_adj = adj & ~water
touch = set(np.unique(prov[land_adj]).tolist()) - {0}

# 州 → 省
p2s = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        p2s[int(x)] = sid

land_ids = [p for p, k in kind.items() if k == 'land']
fake_coast = [p for p in land_ids if coastal.get(p) and p not in touch]
miss_coast = [p for p in land_ids if not coastal.get(p) and p in touch]

print(f'陆地省 {len(land_ids)}；标记沿海 {sum(1 for p in land_ids if coastal.get(p))}')
print(f'\n=== 假沿海（标 true 但不邻海）{len(fake_coast)} 个 ===')
for p in fake_coast[:60]:
    print(f'  p{p}（州 s{p2s.get(p)}）')
print(f'\n=== 漏标沿海（标 false 但实际邻海）{len(miss_coast)} 个 ===')
for p in miss_coast[:60]:
    print(f'  p{p}（州 s{p2s.get(p)}）')

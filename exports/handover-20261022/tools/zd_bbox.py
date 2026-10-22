# -*- coding: utf-8 -*-
"""zd_bbox.py —— 找至冬(SNE)各州省份的像素包围盒，输出裁剪参数到 tools/zd_bbox.npy"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')

sne_states, p2s = {}, {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in (pm.group(1).split() if pm else [])]
    for q in provs:
        p2s[q] = sid
    if om and om.group(1) == 'SNE':
        sne_states[sid] = provs

sne_provs = sorted({q for pv in sne_states.values() for q in pv})
print(f'SNE 州 {len(sne_states)} 个: {sorted(sne_states)}')
print(f'SNE 省 {len(sne_provs)} 个')

rgb2id = {}
for line in open(os.path.join(MOD, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.strip().split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
print(f'definition 颜色 {len(rgb2id)} 条')

import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
arr = np.asarray(Image.open(os.path.join(MOD, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
print(f'provinces.bmp: {W}x{H}')

id2rgb = {v: k for k, v in rgb2id.items()}
missing = [q for q in sne_provs if q not in id2rgb]
print(f'无颜色的 SNE 省: {missing or "无"}')
sne_rgb = [id2rgb[q] for q in sne_provs if q in id2rgb]

key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
u, inv = np.unique(key, return_inverse=True)
rk, gk, bk = (u >> 16) & 255, (u >> 8) & 255, u & 255
sne_mask_u = np.zeros(len(u), dtype=bool)
for (r, g, b) in sne_rgb:
    sne_mask_u |= (rk == r) & (gk == g) & (bk == b)
pix_is_sne = sne_mask_u[inv]
ys, xs = np.nonzero(pix_is_sne)
print(f'SNE 像素: {int(pix_is_sne.sum())}')
print(f'包围盒: x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()}')
print(f'SNE 色块数: {len(np.unique(inv[pix_is_sne]))}')
np.save(os.path.join(ROOT, 'tools', 'zd_bbox.npy'),
        np.array([int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())]))
print('bbox 已存 tools/zd_bbox.npy')

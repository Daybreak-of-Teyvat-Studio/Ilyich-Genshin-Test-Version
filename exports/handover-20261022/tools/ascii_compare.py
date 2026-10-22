# -*- coding: utf-8 -*-
"""ascii_compare.py —— ASCII 对比两版陆地形状 + 关键区域 bbox"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None


def land_mask(base):
    id2rgb, kind = {}, {}
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        a = l.strip().split(';')
        if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
            pid = int(a[0])
            id2rgb[pid] = (int(a[1]), int(a[2]), int(a[3]))
            kind[pid] = a[4]
    arr = np.asarray(Image.open(os.path.join(base, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
    key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    rgb2id = {((r << 16) | (g << 8) | b): pid for pid, (r, g, b) in id2rgb.items()}
    # 只认 land 省颜色
    land_rgb_keys = {((r << 16) | (g << 8) | b) for pid, (r, g, b) in id2rgb.items() if kind.get(pid) == 'land'}
    u = np.unique(key)
    m = np.isin(u, list(land_rgb_keys))
    lut = dict(zip(u.tolist(), m.tolist()))
    land = np.vectorize(lut.get, otypes=[bool])(key)
    return land


for name, base in (('BETA', B), ('GAMMA', G)):
    land = land_mask(base)
    H, W = land.shape
    ys, xs = np.nonzero(land)
    print(f'{name}: {W}x{H} 陆地 bbox x {xs.min()}-{xs.max()}（归一化 {xs.min()/W:.2f}-{xs.max()/W:.2f}）'
          f' y {ys.min()}-{ys.max()}（{ys.min()/H:.2f}-{ys.max()/H:.2f}）')
    small = np.asarray(Image.fromarray((land * 255).astype(np.uint8)).resize((110, 40), Image.BILINEAR)) > 100
    for row in small:
        print('  ' + ''.join('#' if v else '.' for v in row))
    print()

# 关键区域：beta 风龙三州 / gamma s433 的 bbox
def state_bbox(base, sid):
    import glob
    for f in glob.glob(os.path.join(base, 'history', 'states', '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        if int(re.search(r'\bid\s*=\s*(\d+)', t).group(1)) != sid:
            continue
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        provs = [int(x) for x in pm.group(1).split()] if pm else []
        return provs
    return []


def prov_bbox(base, provs):
    id2rgb = {}
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        a = l.strip().split(';')
        if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
            id2rgb[int(a[0])] = (int(a[1]), int(a[2]), int(a[3]))
    arr = np.asarray(Image.open(os.path.join(base, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
    H, W = arr.shape[:2]
    key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    allx, ally = [], []
    for pid in provs:
        if pid not in id2rgb:
            continue
        r, g, b = id2rgb[pid]
        ys, xs = np.nonzero(key == ((r << 16) | (g << 8) | b))
        if len(ys):
            allx += [xs.min(), xs.max()]
            ally += [ys.min(), ys.max()]
    if not allx:
        return None
    return min(allx), max(allx), min(ally), max(ally)


for label, base, sid in (('beta s60 风龙北', B, 60), ('beta s433?', B, 433), ('gamma s433 风龙废墟', G, 433)):
    provs = state_bbox(base, sid)
    bb = prov_bbox(base, provs)
    W = 5632 if base == B else 4096
    H = 2048
    print(f'{label}: 省 {provs[:20]}{"..." if len(provs) > 20 else ""}')
    if bb:
        print(f'  bbox x {bb[0]}-{bb[1]}（归一 {bb[0]/W:.2f}-{bb[1]/W:.2f}） y {bb[2]}-{bb[3]}（{bb[2]/H:.2f}-{bb[3]/H:.2f}）')

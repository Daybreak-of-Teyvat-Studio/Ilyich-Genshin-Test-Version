# -*- coding: utf-8 -*-
"""coord_validate.py —— 坐标桥严格验证（多点投票）
对名称桥 ✓ 的配对，比较坐标桥结果，算一致率。"""
import os, re, sys, json, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None


def load_def(base):
    id2rgb = {}
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        a = l.strip().split(';')
        if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
            id2rgb[int(a[0])] = (int(a[1]), int(a[2]), int(a[3]))
    return id2rgb


def to_prov(base, id2rgb):
    arr = np.asarray(Image.open(os.path.join(base, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
    H, W = arr.shape[:2]
    key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    rgb2id = {((r << 16) | (g << 8) | b): pid for pid, (r, g, b) in id2rgb.items()}
    u, inv = np.unique(key, return_inverse=True)
    pl = np.zeros(len(u), np.int32)
    for i, k in enumerate(u):
        pl[i] = rgb2id.get(int(k), 0)
    return pl[inv].reshape(H, W)


bp = to_prov(B, load_def(B))
gp = to_prov(G, load_def(G))
Hb, Wb = bp.shape
Hg, Wg = gp.shape
SX = Wg / Wb


def map_prov(bid, nsample=24):
    ys, xs = np.nonzero(bp == bid)
    if len(ys) == 0:
        return None, 0
    # 多点投票：按质心周围取样（网格抽样）
    idx = np.linspace(0, len(ys) - 1, min(nsample, len(ys))).astype(int)
    from collections import Counter
    votes = Counter()
    for i in idx:
        gy = int(round(ys[i] * Hg / Hb))
        gx = int(round(xs[i] * SX))
        gid = int(gp[gy, gx])
        if gid:
            votes[gid] += 1
    if not votes:
        return None, 0
    top, n = votes.most_common(1)[0]
    return top, n / sum(votes.values())


# 名称桥 ✓ 配对
br = json.load(open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), encoding='utf-8'))
pairs = [(int(k), v['gamma_pid']) for k, v in br['prov_bridge'].items()
         if str(v.get('status', '')).startswith('✓') and v.get('gamma_pid')]
print(f'名称桥 ✓ 配对数: {len(pairs)}')

agree = 0
disagree = []
sample_dis = []
import random
random.seed(42)
for bid, gn in pairs:
    gid, conf = map_prov(bid)
    if gid == gn:
        agree += 1
    else:
        disagree.append((bid, gn, gid, round(conf, 2)))
print(f'坐标桥与名称桥一致: {agree}/{len(pairs)} = {agree/len(pairs)*100:.1f}%')
print(f'不一致 {len(disagree)} 对（beta省, 名称桥gamma, 坐标桥gamma, 置信）:')
for row in disagree[:25]:
    print('  ', row)

# 检查几个可疑 gamma 省的kind
def kind_of(base, pid):
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        a = l.strip().split(';')
        if a and a[0].strip() == str(pid):
            return f'{a[4]} {a[5]} {a[6]}'
    return '?'
print()
print('gamma p5922:', kind_of(G, 5922), '| gamma p7696:', kind_of(G, 7696), '| gamma p442:', kind_of(G, 442))

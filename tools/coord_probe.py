# -*- coding: utf-8 -*-
"""coord_probe.py —— 坐标桥可行性验证
1) beta/gamma provinces.bmp 尺寸
2) 归一化对齐测试：beta 省份质心 → 缩放到 gamma 帧 → gamma 该处省号
3) 用已知对验证：beta p1314（高塔孤王/风龙）应命中 gamma p442（孤王的高塔）
"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

from PIL import Image
Image.MAX_IMAGE_PIXELS = None

for name, base in (('beta', B), ('gamma', G)):
    p = os.path.join(base, 'map', 'provinces.bmp')
    im = Image.open(p)
    print(f'{name} provinces.bmp: {im.size} {im.mode} {os.path.getsize(p)//1024}KB')

import numpy as np

# beta 省 → RGB（definition.csv）
def load_def(base):
    rgb2id, id2rgb = {}, {}
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        a = l.strip().split(';')
        if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
            rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
            id2rgb[int(a[0])] = (int(a[1]), int(a[2]), int(a[3]))
    return rgb2id, id2rgb

b_rgb2id, b_id2rgb = load_def(B)
g_rgb2id, g_id2rgb = load_def(G)
print(f'beta 省 {len(b_id2rgb)}，gamma 省 {len(g_id2rgb)}')

# 载入 bmp → 省号图
def to_prov(base, id2rgb):
    arr = np.asarray(Image.open(os.path.join(base, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
    H, W = arr.shape[:2]
    key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    rgb2id = {k: v for k, v in (( (r << 16) | (g << 8) | b, pid) for pid, (r, g, b) in id2rgb.items())}
    u, inv = np.unique(key, return_inverse=True)
    pl = np.zeros(len(u), np.int32)
    for i, k in enumerate(u):
        pl[i] = rgb2id.get(int(k), 0)
    return pl[inv].reshape(H, W)

bp = to_prov(B, b_id2rgb)
gp = to_prov(G, g_id2rgb)
Hb, Wb = bp.shape
Hg, Wg = gp.shape
print(f'beta 图 {Wb}x{Hb}，gamma 图 {Wg}x{Hg}，缩放比 x {Wg/Wb:.4f} y {Hg/Hb:.4f}')

# 陆海掩码相关性（粗对齐验证）
b_land = (bp > 0)
g_land = (gp > 0)
from PIL import Image as I2
b_small = np.asarray(I2.fromarray((b_land * 255).astype(np.uint8)).resize((256, 128))) > 127
g_small = np.asarray(I2.fromarray((g_land * 255).astype(np.uint8)).resize((256, 128))) > 127
inter = (b_small & g_small).sum()
union = (b_small | g_small).sum()
print(f'陆海 IoU（粗对齐）: {inter/union:.3f}（>0.8 表示同坐标系）')

# 测试点：beta 省质心 → gamma 帧
def centroid(prov_map, pid):
    ys, xs = np.nonzero(prov_map == pid)
    return (int(round(ys.mean())), int(round(xs.mean())), len(ys))

TESTS = [(1314, 442, '高塔孤王→孤王的高塔'), (4159, None, 'beta s60 内'), (2397, None, ''), (1243, None, 'beta s76'), (4236, None, 'beta s76')]
print()
print('=== 质心映射测试（beta省 → gamma同位置省）===')
for bid, expect, note in TESTS:
    r = centroid(bp, bid)
    if r[2] == 0:
        print(f'  beta p{bid}: 无像素')
        continue
    by, bx, n = r
    gy, gx = int(round(by * Hg / Hb)), int(round(bx * Wg / Wb))
    gid = int(gp[gy, gx])
    ok = '✓' if (expect and gid == expect) or (expect is None) else f'（期望 {expect}）'
    print(f'  beta p{bid} 质心({bx},{by}) → gamma 帧({gx},{gy}) → gamma p{gid}  {ok} {note}')

# gamma p442 反查位置
r = centroid(gp, 442)
print(f'  gamma p442 质心: {r[:2]}')
r = centroid(bp, 1314)
print(f'  beta p1314 质心: {r[:2]}')

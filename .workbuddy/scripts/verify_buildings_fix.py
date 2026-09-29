# -*- coding: utf-8 -*-
"""校验修复后的 buildings.txt 与高度图的吻合度，并出可视化。"""
import struct, os, re, collections
import numpy as np
from PIL import Image, ImageDraw

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
PREV = os.path.join(ROOT, '.workbuddy', 'preview')
REP = os.path.join(ROOT, '.workbuddy', 'report_buildings_verify.txt')
os.makedirs(PREV, exist_ok=True)

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

A, B = 0.09786518, 0.259962
LAND_MIN = 96

raw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
hm = np.frombuffer(raw[o:o + W * H], dtype=np.uint8).reshape(H, W)[::-1]


def sample(x, z):
    fy = H - 1 - z
    fx = x
    if fy < 0 or fy > H - 2 or fx < 0 or fx > W - 2:
        return None
    y0 = int(fy); x0 = int(fx)
    dy = fy - y0; dx = fx - x0
    return (hm[y0, x0] * (1 - dx) + hm[y0, x0 + 1] * dx) * (1 - dy) + \
           (hm[y0 + 1, x0] * (1 - dx) + hm[y0 + 1, x0 + 1] * dx) * dy


def load(p):
    out = []
    for ln in open(p, 'rb').read().split(b'\n'):
        f = ln.rstrip(b'\r').split(b';')
        if len(f) < 6:
            continue
        try:
            out.append((f[1].decode('ascii'), float(f[2]), float(f[3]), float(f[4])))
        except ValueError:
            pass
    return out


def report(recs, tag):
    P(f'--- {tag}  {len(recs):,} 条 ---')
    res_land, res_water = [], []
    for (t, x, y, z) in recs:
        h = sample(x, z)
        if h is None:
            continue
        r = y - (A * h + B)
        if t == 'floating_harbor' or h < LAND_MIN:
            res_water.append(r)
        else:
            res_land.append(r)
    for nm, r in (('陆地建筑', res_land), ('水面建筑(港口/水下点)', res_water)):
        r = np.array(r)
        if not len(r):
            continue
        P(f'   {nm}: {len(r):,} 条   mean|r|={np.abs(r).mean():.4f}  '
          f'|r|>0.5 的 {int((np.abs(r) > 0.5).sum()):,}   max|r|={np.abs(r).max():.3f}')
    return np.array(res_land)


new = load(os.path.join(MAP, 'buildings.txt'))
old = load(os.path.join(ROOT, '.workbuddy', 'backup_20260924_1625', 'buildings.txt'))
P('=== 修复前后对比（残差 = y - (A*h+B)，h 取现行 heightmap.bmp）===')
report(old, '修复前')
report(new, '修复后')

# 挪动清单
moved = []
for a, b in zip(old, new):
    if a[1] == b[1] and a[3] == b[3] and abs(a[2] - b[2]) > 0.005:
        moved.append((b[0], b[1], b[3], a[2], b[2], b[2] - a[2]))
P('')
P(f'=== 本次实际挪动的建筑 {len(moved):,} 条（按 |Δ| 排序前 15）===')
for (t, x, z, y0, y1, d) in sorted(moved, key=lambda q: -abs(q[5]))[:15]:
    P(f'   {t:<30} x={x:8.2f} z={z:8.2f}  y {y0:7.2f} -> {y1:7.2f}  Δ={d:+7.3f}')

# ---- 可视化 ----
im = Image.open(os.path.join(MAP, 'terrain.bmp'))
base = im.convert('RGB').resize((1024, 512), Image.NEAREST)
d = ImageDraw.Draw(base)
for (t, x, z, y0, y1, dd) in moved:
    px = x * 1024.0 / W
    py = (H - 1 - z) * 512.0 / H
    col = (255, 0, 0) if dd > 0 else (0, 0, 255)
    d.ellipse([px - 4, py - 4, px + 4, py + 4], outline=col, width=2)
base.save(os.path.join(PREV, 'buildings_fix_overview.png'))

# 两个热点区放大
hot = [(2496, 831), (2240, 703)]
tiles = []
for (cx, cz) in hot:
    r0 = int(H - 1 - cz) - 96; c0 = int(cx) - 96
    r0 = max(0, min(H - 193, r0)); c0 = max(0, min(W - 193, c0))
    crop = base.crop((int(c0 * 1024.0 / W), int(r0 * 512.0 / H),
                      int((c0 + 192) * 1024.0 / W), int((r0 + 192) * 512.0 / H)))
    crop = crop.resize((420, 420), Image.NEAREST)
    tiles.append(crop)
cmp_im = Image.new('RGB', (860, 440), (255, 255, 255))
cmp_im.paste(tiles[0], (5, 10)); cmp_im.paste(tiles[1], (435, 10))
cmp_im.save(os.path.join(PREV, 'buildings_fix_hotspots.png'))

P('')
P(f'挪动建筑的分布（128px 格，前 10）:')
g = collections.Counter()
for (t, x, z, y0, y1, dd) in moved:
    g[(int(x // 128), int((H - 1 - z) // 128))] += 1
for (gx, gy), c in g.most_common(10):
    P(f'   图元 x≈{gx*128+64:<6} z≈{H-1-(gy*128+64):<6}  {c} 条')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

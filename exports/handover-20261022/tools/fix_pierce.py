# -*- coding: utf-8 -*-
"""
防穿模抬升 v4 —— 物理判据：模型嵌在坡里（footprint 大部分地面高于基座）才抬。

规则：
  · naval 类 / 浮港 / 中心 h<96：不动
  · 7x7 邻域内海洋像素（h<90）占比 >25%：海岸/悬崖建筑，抬高会悬空 → 不动
  · fp90 = 7x7 邻域高度的 90 分位；y_fp = A*fp90+B
    y_fp - y_cur > 1.0 → y_new = max(y_cur, y_fp)   （90 分位而非 max，留余量防悬空）
  · 字节级保持 CRLF，只改第 4 列
"""
import os, sys, shutil, datetime, collections
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version')
from fix_buildings_height import read_heightmap, bilinear, A, B, SEA_LEVEL, SKIP_TYPES

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BP = os.path.join(G, 'map', 'buildings.txt')
RAD, SEA_FRAC, TH = 3, 0.25, 1.0
NAVAL = {'dockyard', 'naval_base_spawn', 'naval_supply_hub', 'naval_headquarters',
         'coastal_bunker', 'floating_harbor'}

hm, W, H = read_heightmap(os.path.join(G, 'map', 'heightmap.bmp'), flip=False)
raw = open(BP, 'rb').read()
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
        out.append(ln); continue
    try:
        btype, x, y, z = f[1], float(f[2]), float(f[3]), float(f[4])
    except ValueError:
        out.append(ln); continue
    st['total'] += 1
    if btype in SKIP_TYPES or btype in NAVAL:
        st['naval'] += 1; out.append(ln); continue
    h_c, _ = bilinear(hm, x, z)
    if h_c < 96:
        st['sea'] += 1; out.append(ln); continue
    r0, c0 = int(round(z)) % H, int(round(x)) % W
    if sea_frac[r0, c0] > SEA_FRAC:
        st['coast'] += 1; out.append(ln); continue
    y_fp = A * fp90[r0, c0] + B
    if y_fp - y > TH:
        f[3] = f'{max(y, y_fp):.2f}'
        st['lift'] += 1
        samples.append((y_fp - y, btype, x, z, y))
    else:
        st['keep'] += 1
    out.append(ln)

blob = '\r\n'.join(out)
bdir = os.path.join(ROOT, '.backups', 'buildings_lift_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(BP, os.path.join(bdir, 'buildings.txt'))
open(BP, 'w', encoding='utf-8', newline='').write(blob)
nb = open(BP, 'rb').read()
print(f"统计: 总 {st['total']} / naval浮港 {st['naval']} / 水面 {st['sea']} / 海岸跳过 {st['coast']} / "
      f"保持 {st['keep']} / 抬升 {st['lift']}")
print(f'字节 {len(raw)} -> {len(nb)}（{len(nb)-len(raw):+d}）；CRLF {nb.count(bytes([13,10]))}；BOM {nb[:3]==bytes([239,187,191])}')
print('抬升量分布:')
dd = collections.Counter()
for d, *_ in samples:
    dd[min(6, int(d))] += 1
print('   ' + str(dict(sorted(dd.items()))))
for d, bt, x, z, yo in sorted(samples, reverse=True)[:6]:
    print(f'   {bt:30s} ({x:.0f},{z:.0f})  {yo:.2f} -> {yo+d:.2f}  (+{d:.2f})')
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
rgb2id = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)
byp = collections.Counter()
for d, bt, x, z, yo in samples:
    byp[int(prov[int(round(H - z)), int(round(x))])] += 1
print(f'涉及省 {len(byp)}；点名 762/1766/412: {byp.get(762,0)}/{byp.get(1766,0)}/{byp.get(412,0)}')
print(f'备份: {bdir}')

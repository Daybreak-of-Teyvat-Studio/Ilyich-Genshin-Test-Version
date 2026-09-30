# -*- coding: utf-8 -*-
"""terrain.bmp 体检：模式/尺寸/调色板/与 09-27 备份的像素差异"""
import os, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
BAK = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups\terrain_20260927_103440'

cur_p = os.path.join(G, 'map', 'terrain.bmp')
bak_p = os.path.join(BAK, 'terrain_new.bmp')

for label, p in (('当前', cur_p), ('09-27 备份', bak_p)):
    img = Image.open(p)
    print(f'=== {label} ===')
    print(f'  format={img.format} mode={img.mode} size={img.size}')
    raw = open(p, 'rb').read()
    print(f'  文件头: {raw[:2]}  位深标记={raw[28:30].hex()}  '
          f'调色板偏移数据={raw[54:58].hex()}')
    if img.mode == 'P':
        pal = img.getpalette()
        print(f'  调色板前 6 色: {pal[:18]}')
    arr = np.asarray(img)
    import collections
    c = collections.Counter(arr.ravel().tolist())
    print(f'  索引分布: {dict(sorted(c.items(), key=lambda x: -x[1]))}')
    print()

# 像素差异
a = np.asarray(Image.open(cur_p))
b = np.asarray(Image.open(bak_p))
if a.shape == b.shape:
    d = int((a != b).sum())
    print(f'像素差异总数: {d}')
    if d:
        ys, xs = np.nonzero(a != b)
        print(f'差异范围: x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()}')
        # 统计差异对
        import collections
        pairs = collections.Counter(zip(a[ys, xs].tolist(), b[ys, xs].tolist()))
        print('差异对 (现→备):', dict(list(pairs.items())[:10]))
else:
    print(f'尺寸不同: {a.shape} vs {b.shape}')

# 调色板对比
pa = Image.open(cur_p).getpalette()
pb = Image.open(bak_p).getpalette()
if pa and pb:
    same = pa[:768] == pb[:768]
    print(f'调色板一致: {same}')
    if not same:
        diffs = [(i, pa[i], pb[i]) for i in range(min(len(pa), len(pb))) if pa[i] != pb[i]]
        print(f'调色板差异条目 {len(diffs)}，前 10: {diffs[:10]}')

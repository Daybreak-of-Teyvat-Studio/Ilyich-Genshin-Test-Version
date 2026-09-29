# -*- coding: utf-8 -*-
"""把 buildings.txt 的坐标画到 provinces.bmp 上，验证它们落在哪；输出直观对比图。"""
import struct, os, collections
import numpy as np
from PIL import Image, ImageDraw

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
PREV = os.path.join(ROOT, '.workbuddy', 'preview')
os.makedirs(PREV, exist_ok=True)

im = Image.open(os.path.join(MAP, 'provinces.bmp')).convert('RGB')
W, H = im.size
print('provinces.bmp', W, H)

bl = []
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        bl.append((int(f[0]), float(f[2]), float(f[4])))
    except ValueError:
        pass
print('建筑', len(bl))

# 真值：positions.txt 坐标
import re
pos = {}
cur = None; seen = False
for ln in open(os.path.join(MAP, 'positions.txt'), 'rb'):
    s = ln.decode('ascii', 'replace').strip()
    m = re.match(r'^(\d+)=\{$', s)
    if m:
        cur = int(m.group(1)); seen = False; continue
    if cur is not None and not seen:
        mm = re.match(r'^([\d.]+)\s+([\d.]+)\s+([\d.]+)$', s)
        if mm:
            pos[cur] = (float(mm.group(1)), float(mm.group(3))); seen = True

base = im.resize((1024, 512), Image.LANCZOS)
for tag, fn, col in (('bmap_row_z', lambda z: (int(z)), (255, 0, 0)),
                     ('bmap_row_flip', lambda z: (H - 1 - int(z)), (0, 0, 255))):
    ov = base.copy()
    d = ImageDraw.Draw(ov)
    for (pid, x, z) in bl[::10]:
        px = x * 1024.0 / W
        py = fn(z) * 512.0 / H
        d.point((px, py), fill=col)
    # 叠加 positions 真值（绿）
    for pid, (x, z) in pos.items():
        px = x * 1024.0 / W
        py = z * 512.0 / H
        d.ellipse([px - 1, py - 1, px + 1, py + 1], fill=(0, 255, 0))
    ov.save(os.path.join(PREV, f'{tag}.png'))
    print('saved', tag)

# 也把 24bit 原始地形图作底
print('done')

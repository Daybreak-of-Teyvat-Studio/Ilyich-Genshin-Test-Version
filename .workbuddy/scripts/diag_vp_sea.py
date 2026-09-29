# -*- coding: utf-8 -*-
"""生成两类悬空的对照图：
 A) 胜利点：847 个正常（绿）+ 14 个落海（红）画在地形/高度图上；
 B) 建筑：陆地建筑（绿）+ 落海建筑（红）画在地形图上。
"""
import struct, os, re, collections
import numpy as np
from PIL import Image, ImageDraw

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
PREV = os.path.join(ROOT, '.workbuddy', 'preview')
os.makedirs(PREV, exist_ok=True)

# 用 24 位画稿当底（好看）
im = Image.open(os.path.join(MAP, 'terrain_00.bmp')).convert('RGB')
W, H = im.size
print('bottom', W, H, im.mode)

hmraw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
ho = struct.unpack_from('<I', hmraw, 10)[0]
hm = np.frombuffer(hmraw, dtype=np.uint8, offset=ho)[:W * H].reshape(H, W)
LAND = hm >= 96

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

vp = {}
for dp, _, fs in os.walk(os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')):
    for fn in fs:
        if fn.endswith('.txt'):
            for ln in open(os.path.join(dp, fn), encoding='utf-8', errors='replace'):
                s = ln.split('#')[0].strip()
                if 'victory_points' in s and '=' in s:
                    n = re.findall(r'-?\d+', s.split('=', 1)[1])
                    if len(n) >= 2:
                        vp[int(n[0])] = int(n[1])
print('VP', len(vp))

base = im.resize((1024, 512), Image.LANCZOS)
ov = base.copy(); d = ImageDraw.Draw(ov)
bad_list = []
for pid in vp:
    if pid not in pos:
        continue
    x, z = pos[pid]
    px = x * 1024.0 / W; py = z * 512.0 / H
    on = LAND[int(z), int(x)]
    if on:
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(0, 200, 0), outline=(0, 0, 0))
    else:
        d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=(255, 0, 0), outline=(255, 255, 0), width=2)
        bad_list.append(pid)
ov.save(os.path.join(PREV, 'vp_onland.png'))
print('VP 落海:', bad_list)

# 建筑
ov2 = base.copy(); d2 = ImageDraw.Draw(ov2)
nb = 0
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        t = f[1]; x = float(f[2]); z = float(f[4])
    except ValueError:
        continue
    px = x * 1024.0 / W; py = z * 512.0 / H
    if not LAND[int(z), int(x)]:
        d2.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 0, 0))
        nb += 1
ov2.save(os.path.join(PREV, 'buildings_onland.png'))
print('建筑落海', nb)

# 放大 14 个胜利点落海的位置
tiles = []
for pid in bad_list[:14]:
    x, z = pos[pid]
    c0 = max(0, min(W - 257, int(x) - 128)); r0 = max(0, min(H - 257, int(z) - 128))
    crop = im.crop((c0, r0, c0 + 256, r0 + 256)).resize((300, 300), Image.NEAREST)
    dd = ImageDraw.Draw(crop)
    mx = (x - c0) * 300 / 256; my = (z - r0) * 300 / 256
    dd.line([mx - 20, my, mx + 20, my], fill=(255, 0, 0), width=3)
    dd.line([mx, my - 20, mx, my + 20], fill=(255, 0, 0), width=3)
    dd.ellipse([mx - 8, my - 8, mx + 8, my + 8], outline=(255, 255, 0), width=3)
    dd.text((5, 5), f'P{pid}', fill=(255, 255, 255))
    tiles.append(crop)
cols = 5
rows = (len(tiles) + cols - 1) // cols
fig = Image.new('RGB', (cols * 304, rows * 304), (30, 30, 30))
for i, t in enumerate(tiles):
    fig.paste(t, ((i % cols) * 304, (i // cols) * 304))
fig.save(os.path.join(PREV, 'vp_sea_mosaic.png'))
print('saved mosaic', fig.size, 'tiles', len(tiles))

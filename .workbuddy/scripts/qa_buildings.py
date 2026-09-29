# -*- coding: utf-8 -*-
"""出修复对照图（以高度图为底，直观判断建筑是否落地）并量化 positions.txt 的高度问题。"""
import struct, os, re, collections
import numpy as np
from PIL import Image, ImageDraw

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
PREV = os.path.join(ROOT, '.workbuddy', 'preview')
REP = os.path.join(ROOT, '.workbuddy', 'report_positions_check.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

A, B = 0.09786518, 0.259962

raw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
T = np.frombuffer(raw[o:o + W * H], dtype=np.uint8).reshape(H, W)[::-1]


def sample(x, z):
    fy = H - 1 - z; fx = x
    if fy < 0 or fy > H - 2 or fx < 0 or fx > W - 2:
        return None
    y0 = int(fy); x0 = int(fx); dy = fy - y0; dx = fx - x0
    return (T[y0, x0] * (1 - dx) + T[y0, x0 + 1] * dx) * (1 - dy) + \
           (T[y0 + 1, x0] * (1 - dx) + T[y0 + 1, x0 + 1] * dx) * dy


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


old = load(os.path.join(ROOT, '.workbuddy', 'backup_20260924_1625', 'buildings.txt'))
new = load(os.path.join(MAP, 'buildings.txt'))

# 高度图灰度底图
base = Image.fromarray(T, mode='L').convert('RGB')
small = base.resize((1024, 512), Image.LANCZOS)

hot = [(2496, 831), (2240, 703)]
tiles = []
for (cx, cz) in hot:
    r0 = max(0, min(H - 257, int(H - 1 - cz) - 128)); c0 = max(0, min(W - 257, cx - 128))
    crop = base.crop((c0, r0, c0 + 256, r0 + 256)).resize((512, 512), Image.NEAREST)
    dl = ImageDraw.Draw(crop)
    for (t, x, y, z) in old:
        px = x - c0; py = (H - 1 - z) - r0
        if 0 <= px < 256 and 0 <= py < 256:
            if t == 'floating_harbor':
                continue
            dl.ellipse([px * 2 - 3, py * 2 - 3, px * 2 + 3, py * 2 + 3], fill=(255, 80, 80))
    dr = ImageDraw.Draw(crop)
    for (t, x, y, z) in new:
        px = x - c0; py = (H - 1 - z) - r0
        if 0 <= px < 256 and 0 <= py < 256:
            if t == 'floating_harbor':
                continue
            dr.ellipse([px * 2 - 2, py * 2 - 2, px * 2 + 2, py * 2 + 2], fill=(0, 90, 0))
    tiles.append(crop)

fig = Image.new('RGB', (1060, 540), (255, 255, 255))
fig.paste(tiles[0], (10, 14)); fig.paste(tiles[1], (540, 14))
fig.save(os.path.join(PREV, 'buildings_fix_qa.png'))

# 全图：只画"挪动过"的建筑，落在高度图上
ov = base.resize((1024, 512), Image.LANCZOS)
dm = ImageDraw.Draw(ov)
n_move = 0
for a, b in zip(old, new):
    if a[1] == b[1] and a[3] == b[3] and abs(a[2] - b[2]) > 0.005:
        n_move += 1
        px = b[1] * 1024.0 / W; py = (H - 1 - b[3]) * 512.0 / H
        dm.ellipse([px - 3, py - 3, px + 3, py + 3], outline=(255, 0, 0), width=2)
ov.save(os.path.join(PREV, 'buildings_fix_onheight.png'))
P(f'挪动建筑 {n_move:,} 条已标在全图 {os.path.join(PREV, "buildings_fix_onheight.png")}')

# ---------- positions.txt ----------
P('')
P('=== positions.txt 核查 ===')
pt = os.path.join(MAP, 'positions.txt')
blocks = 0
diffs = []
cur_id = None
seen = False
with open(pt, 'rb') as f:
    for ln in f:
        s = ln.decode('ascii', 'replace').strip()
        m = re.match(r'^(\d+)=\{$', s)
        if m:
            cur_id = int(m.group(1)); seen = False; blocks += 1
            continue
        if cur_id is not None and not seen:
            mm = re.match(r'^([\d.]+)\s+([\d.]+)\s+([\d.]+)$', s)
            if mm:
                x, y, z = float(mm.group(1)), float(mm.group(2)), float(mm.group(3))
                h = sample(x, z)
                if h is not None:
                    ys = A * h + B
                    diffs.append((cur_id, x, z, h, y, ys))
                seen = True
P(f'   省份块 {blocks:,} 个，取到位置 {len(diffs):,} 个')
dv = np.array([q[5] - q[4] for q in diffs])
P(f'   位置 y 一律 {sorted(set(round(q[4],3) for q in diffs))[:5]}')
P(f'   按高度图应取的值与现值的差 Δ: mean={dv.mean():+.3f}  mean|Δ|={np.abs(dv).mean():.4f}  min={dv.min():+.2f}  max={dv.max():+.2f}')
for th in (0.5, 1.0, 2.0, 5.0, 10.0):
    P(f'   |Δ|>{th:<5}: {int((np.abs(dv) > th).sum()):,} 个省份')
P('   差值最大的 12 个省份:')
for q in sorted(diffs, key=lambda t: -abs(t[5] - t[4]))[:12]:
    P(f'      省{q[0]:<6} x={q[1]:8.2f} z={q[2]:8.2f} h={q[3]:6.1f}  现 y={q[4]:6.3f}  应为={q[5]:6.3f}  Δ={q[5]-q[4]:+7.3f}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

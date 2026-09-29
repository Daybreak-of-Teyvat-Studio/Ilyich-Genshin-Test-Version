# -*- coding: utf-8 -*-
"""修复后验证 + 出对照图。"""
import struct, os, re, collections
import numpy as np
from PIL import Image, ImageDraw

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
PREV = os.path.join(ROOT, '.workbuddy', 'preview')
REP = os.path.join(ROOT, '.workbuddy', 'report_verify_after.txt')
os.makedirs(PREV, exist_ok=True)

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

A, B = 0.09786518, 0.259962

raw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
ho = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
hm = np.frombuffer(raw, dtype=np.uint8, offset=ho)[:W * H].reshape(H, W)

rawp = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
po = struct.unpack_from('<I', rawp, 10)[0]
rb = W * 3
a = np.frombuffer(rawp, dtype=np.uint8, offset=po)[:rb * H].reshape(H, W, 3)
prov = (a[:, :, 2].astype(np.int32) << 16) | (a[:, :, 1].astype(np.int32) << 8) | a[:, :, 0].astype(np.int32)
rgb2pid, pid_type = {}, {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) >= 5:
            try:
                rgb2pid[(int(f2[1]) << 16) | (int(f2[2]) << 8) | int(f2[3])] = int(f2[0])
                pid_type[int(f2[0])] = f2[4]
            except ValueError:
                pass
LAND = hm >= 96

def bilinear(x, z):
    r0 = int(z); c0 = int(x)
    if r0 < 0 or r0 > H - 2 or c0 < 0 or c0 > W - 2:
        return None
    dr = z - r0; dc = x - c0
    return (hm[r0, c0] * (1 - dc) + hm[r0, c0 + 1] * dc) * (1 - dr) + \
           (hm[r0 + 1, c0] * (1 - dc) + hm[r0 + 1, c0 + 1] * dc) * dr

# ---- 1. 建筑残差复检 ----
P('=== 1. 修复后 buildings.txt 残差复检（row=z）===')
cnt = collections.Counter()
res = []
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        t = f[1]; x = float(f[2]); y = float(f[3]); z = float(f[4])
    except ValueError:
        continue
    cnt['总'] += 1
    if not (0 <= int(x) < W and 0 <= int(z) < H):
        cnt['越界'] += 1; continue
    cnt['陆上像素'] += int(LAND[int(z), int(x)])
    cnt['海上像素'] += int(not LAND[int(z), int(x)])
    if t == 'floating_harbor':
        cnt['floating_harbor'] += 1; continue
    h = bilinear(x, z)
    if h is None:
        continue
    res.append(y - (A * h + B))
r = np.array(res)
P(f'   总记录 {cnt["总"]:,}  陆上 {cnt["陆上像素"]:,}  海上 {cnt["海上像素"]:,}  '
  f'（其中 floating_harbor {cnt["floating_harbor"]:,}）')
P(f'   非浮港建筑残差: {len(r):,} 条  mean|r|={np.abs(r).mean():.6f}  max|r|={np.abs(r).max():.6f}')
for th in (0.01, 0.1, 0.5, 1.0):
    P(f'      |r|>{th}: {int((np.abs(r)>th).sum()):,}')

# ---- 2. 胜利点坐标复检 ----
P('')
P('=== 2. 修复后 positions.txt 胜利点复检 ===')
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

# 全图命中率
tot = hit = 0
for pid, (x, z) in pos.items():
    tot += 1
    if rgb2pid.get(int(prov[int(z), int(x)])) == pid:
        hit += 1
P(f'   全图 positions -> 本省像素: {hit:,}/{tot:,} = {100.0*hit/tot:.2f}%')

c = collections.Counter(); still = []
for pid in vp:
    if pid not in pos:
        continue
    x, z = pos[pid]
    on = LAND[int(z), int(x)]
    got = rgb2pid.get(int(prov[int(z), int(x)]))
    c['总'] += 1
    c['在陆地'] += int(on)
    c['落本省'] += int(got == pid)
    if not on or got != pid:
        still.append((pid, x, z, on, got))
P(f'   胜利点省 {c["总"]}  坐标在陆地 {c["在陆地"]}  坐标落本省 {c["落本省"]}')
P(f'   仍异常 {len(still)}: {still}')

# ---- 3. 对照图 ----
P('')
im = Image.open(os.path.join(MAP, 'terrain_00.bmp')).convert('RGB')
base = im.resize((1024, 512), Image.LANCZOS)
ov = base.copy(); d = ImageDraw.Draw(ov)
BAD_OLD = {222: (2483.468, 700.106), 674: (1477.0, 606.0), 688: (2456.0, 769.0),
           774: (1748.514, 1585.429), 860: (2646.092, 867.075), 1269: (1557.942, 1169.654),
           1752: (1465.337, 1017.326), 2435: (1826.0, 604.0), 2473: (1967.923, 1699.215),
           3055: (1685.04, 1201.42), 3939: (1612.805, 701.138), 4680: (1934.0, 891.0),
           4689: (2484.667, 687.2), 4691: (1458.0, 567.0)}
for pid, (ox, oz) in BAD_OLD.items():
    pxx = ox * 1024.0 / W; pyy = oz * 512.0 / H
    d.ellipse([pxx - 5, pyy - 5, pxx + 5, pyy + 5], outline=(255, 0, 0), width=2)
for pid in BAD_OLD:
    if pid in pos:
        nx, nz = pos[pid]
        pxx = nx * 1024.0 / W; pyy = nz * 512.0 / H
        d.ellipse([pxx - 3, pyy - 3, pxx + 3, pyy + 3], fill=(0, 255, 0), outline=(255, 255, 0))
ov.save(os.path.join(PREV, 'vp_fixed_map.png'))
P(f'   对照图 -> {os.path.join(PREV, "vp_fixed_map.png")}  (红=旧位置, 绿=新位置)')

# 放大 14 处修复前后
tiles = []
for pid in sorted(BAD_OLD):
    ox, oz = BAD_OLD[pid]
    c0 = max(0, min(W - 193, int(ox) - 96)); r0 = max(0, min(H - 193, int(oz) - 96))
    crop = im.crop((c0, r0, c0 + 192, r0 + 192)).resize((280, 280), Image.NEAREST)
    dd = ImageDraw.Draw(crop)
    for (cx, cz), col, w in (((ox, oz), (255, 0, 0), 2), (pos[pid], (0, 255, 0), 3)):
        mx = (cx - c0) * 280 / 192; my = (cz - r0) * 280 / 192
        dd.line([mx - 14, my, mx + 14, my], fill=col, width=w)
        dd.line([mx, my - 14, mx, my + 14], fill=col, width=w)
    dd.text((5, 5), f'P{pid}', fill=(255, 255, 255))
    tiles.append(crop)
cols = 5
rows = (len(tiles) + cols - 1) // cols
fig = Image.new('RGB', (cols * 284, rows * 284), (30, 30, 30))
for i, t in enumerate(tiles):
    fig.paste(t, ((i % cols) * 284, (i // cols) * 284))
fig.save(os.path.join(PREV, 'vp_fixed_mosaic.png'))
P(f'   放大对照 -> {os.path.join(PREV, "vp_fixed_mosaic.png")}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

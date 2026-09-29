# -*- coding: utf-8 -*-
"""标定：buildings.txt 的 (x,z) 打到 heightmap 时该用哪种 row 映射。
判据：建筑应该建在「陆地」上（除了 floating_harbor）。
用两种映射分别采样 h，看哪种映射下「绝大数非浮动港口建筑的 h>=96」。"""
import struct, os
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')

raw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
ho = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
hm = np.frombuffer(raw, dtype=np.uint8, offset=ho)[:W * H].reshape(H, W)
print(f'heightmap {W}x{H}')

bl = []
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        bl.append((f[1], float(f[2]), float(f[4])))
    except ValueError:
        pass
print('建筑', len(bl))

for tag, fn in (('row=z', lambda z: int(z)), ('row=H-1-z', lambda z: H - 1 - int(z))):
    cnt = {'land': 0, 'water': 0, 'float': 0}
    for (t, x, z) in bl:
        r = fn(z); c = int(x)
        if not (0 <= c < W and 0 <= r < H):
            continue
        if t == 'floating_harbor':
            cnt['float'] += 1
            continue
        if hm[r, c] >= 96:
            cnt['land'] += 1
        else:
            cnt['water'] += 1
    tot = cnt['land'] + cnt['water']
    print(f'  {tag:<12} 非浮港建筑 陆上={cnt["land"]:,}  水下={cnt["water"]:,}  '
          f'陆上占比={100.0*cnt["land"]/tot:.2f}%   (浮港 {cnt["float"]:,})')

# 同时用「建筑号一致」判定：不同映射下，建筑是否落在它声明的省的像素上
rawp = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
po = struct.unpack_from('<I', rawp, 10)[0]
rb = W * 3
a = np.frombuffer(rawp, dtype=np.uint8, offset=po)[:rb * H].reshape(H, W, 3)
prov = (a[:, :, 2].astype(np.int32) << 16) | (a[:, :, 1].astype(np.int32) << 8) | a[:, :, 0].astype(np.int32)
rgb2pid = {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) >= 5:
            try:
                rgb2pid[(int(f2[1]) << 16) | (int(f2[2]) << 8) | int(f2[3])] = int(f2[0])
            except ValueError:
                pass

# 用 positions 的「省坐标 -> 省份像素」= row=z 已证；那建筑呢？
pos = {}
import re
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

# 关键：对每个有建筑的省，比较「建筑质心到本省像素的距离」
# 用两种映射下，建筑点距离该省像素集的距离
print()
print('=== 建筑点到「本省像素集」的距离（两种映射）===')
import collections
pid2pts = collections.defaultdict(list)
for (t, x, z) in bl:
    pass
bp = collections.defaultdict(list)
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        bp[int(f[0])].append((float(f[2]), float(f[4])))
    except ValueError:
        pass

# 省像素的范围
pids = np.array([rgb2pid.get(int(q), -1) for q in prov.ravel()])
rng = {}
ys, xs = np.where(prov > 0)
vv = prov[ys, xs]
pp = np.array([rgb2pid.get(int(q), -1) for q in vv])
order = np.argsort(pp)
pp_s = pp[order]; ys_s = ys[order]; xs_s = xs[order]
uniq, starts = np.unique(pp_s, return_index=True)
starts = list(starts) + [len(pp_s)]
for i, p in enumerate(uniq):
    if p < 0:
        continue
    seg_y = ys_s[starts[i]:starts[i + 1]]; seg_x = xs_s[starts[i]:starts[i + 1]]
    rng[p] = (seg_y.min(), seg_y.max(), seg_x.min(), seg_x.max())

for tag, fn in (('row=z', lambda z: z), ('row=H-1-z', lambda z: H - 1 - z)):
    tot = inside = 0
    for pid, lst in bp.items():
        if pid not in rng:
            continue
        r0, r1, c0, c1 = rng[pid]
        for (x, z) in lst:
            rr = fn(z)
            tot += 1
            if r0 - 2 <= rr <= r1 + 2 and c0 - 2 <= x <= c1 + 2:
                inside += 1
    print(f'  {tag:<12} 落在本省包围盒(±2)内 {inside:,}/{tot:,} = {100.0*inside/tot:.2f}%')

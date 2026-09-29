# -*- coding: utf-8 -*-
"""按偏差大小分类：哪些省的 buildings 坐标与 positions 坐标对得上，哪些不。"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_bmap3.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

raw = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
rb = W * 3
a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:rb * H].reshape(H, W, 3)
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

bp = collections.defaultdict(list)
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        bp[int(f[0])].append((float(f[2]), float(f[4]), f[1]))
    except ValueError:
        pass

P('=== 逐省：建筑均值坐标 vs positions 坐标，并按「是否落在本省像素」判定 ===')
res = []
for pid, lst in bp.items():
    ar = np.array([(q[0], q[1]) for q in lst])
    bx, bz = ar[:, 0].mean(), ar[:, 1].mean()
    px, pz = pos.get(pid, (None, None))
    # 判定：建筑坐标打在 provinces 上落在哪个省
    c = int(bx); r = int(bz)
    got_z = rgb2pid.get(int(prov[r, c])) if (0 <= c < W and 0 <= r < H) else None
    c2 = int(bx); r2 = H - 1 - int(bz)
    got_f = rgb2pid.get(int(prov[r2, c2])) if (0 <= c2 < W and 0 <= r2 < H) else None
    res.append((pid, bx, bz, px, pz, got_z, got_f, len(lst)))

n_self_z = sum(1 for q in res if q[5] == q[0])
n_self_f = sum(1 for q in res if q[6] == q[0])
P(f'   省数 {len(res)}')
P(f'   建筑坐标(row=z) 落在本省: {n_self_z}')
P(f'   建筑坐标(row=H-1-z) 落在本省: {n_self_f}')
P(f'   两者都不在: {sum(1 for q in res if q[5]!=q[0] and q[6]!=q[0])}')

P('')
P('=== 逐条建筑判定 ===')
tot = z_ok = f_ok = neither = 0
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        pid = int(f[0]); x = float(f[2]); z = float(f[4])
    except ValueError:
        continue
    tot += 1
    c = int(x); r = int(z)
    c2 = int(x); r2 = H - 1 - int(z)
    a1 = (0 <= c < W and 0 <= r < H and rgb2pid.get(int(prov[r, c])) == pid)
    a2 = (0 <= c2 < W and 0 <= r2 < H and rgb2pid.get(int(prov[r2, c2])) == pid)
    if a1: z_ok += 1
    if a2: f_ok += 1
    if not a1 and not a2: neither += 1
P(f'   总 {tot:,}   row=z 命中 {z_ok:,}   row=H-1-z 命中 {f_ok:,}   都不中 {neither:,}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

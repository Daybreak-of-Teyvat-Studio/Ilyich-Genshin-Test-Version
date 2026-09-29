# -*- coding: utf-8 -*-
"""标定 buildings.txt 的坐标映射：穷举线性变换 + 逐省质心/包围盒比对。"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')

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

# 每个省的质心 (row, col) 与包围盒
print('=== 计算各省质心/包围盒 ===')
pid2rows = collections.defaultdict(list)
ys, xs = np.where(prov > 0)
v = prov[ys, xs]
pids = np.array([rgb2pid.get(int(q), -1) for q in v])
for i in range(len(ys)):
    p = pids[i]
    if p >= 0:
        pid2rows[p].append((ys[i], xs[i]))
print(f'   有像素的省 {len(pid2rows):,}')

cent = {}
for p, lst in pid2rows.items():
    ar = np.array(lst)
    cent[p] = (float(ar[:, 0].mean()), float(ar[:, 1].mean()),
               int(ar[:, 0].min()), int(ar[:, 0].max()), int(ar[:, 1].min()), int(ar[:, 1].max()))

# 取 buildings.txt 里每省第一条
bprov = {}
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        pid = int(f[0]); x = float(f[2]); z = float(f[4])
    except ValueError:
        continue
    if pid not in bprov:
        bprov[pid] = (x, z)
print(f'   buildings.txt 覆盖省 {len(bprov):,}')

print()
print('=== 拿 buildings 的 (x,z) 与省质心/包围盒比对 ===')
rows_ = []
for pid, (x, z) in list(bprov.items())[:60]:
    if pid in cent:
        cr, cc, r0, r1, c0, c1 = cent[pid]
        rows_.append((pid, x, z, cc, cr, c0, c1, r0, r1))

print(f'{"pid":<8}{"bx":>9}{"bz":>9} | {"质心col":>9}{"质心row":>9} | {"col范围":>14}{"row范围":>14}')
for (pid, x, z, cc, cr, c0, c1, r0, r1) in rows_[:40]:
    print(f'{pid:<8}{x:>9.1f}{z:>9.1f} | {cc:>9.1f}{cr:>9.1f} | {f"{c0}-{c1}":>14}{f"{r0}-{r1}":>14}')

print()
print('=== 判断：bz ≈ cr ? 还是 bz ≈ H-1-cr ? ===')
d1 = [abs(z - cr) for (pid, x, z, cc, cr, c0, c1, r0, r1) in rows_]
d2 = [abs(z - (H - 1 - cr)) for (pid, x, z, cc, cr, c0, c1, r0, r1) in rows_]
dx = [abs(x - cc) for (pid, x, z, cc, cr, c0, c1, r0, r1) in rows_]
print(f'   |bz - 质心row|        mean={np.mean(d1):.1f}')
print(f'   |bz - (H-1-质心row)|  mean={np.mean(d2):.1f}')
print(f'   |bx - 质心col|        mean={np.mean(dx):.1f}')

# 全局：省1 的像素范围
print()
print('=== 省 1 的包围盒 ===')
if 1 in cent:
    print('   ', cent[1])

open(os.path.join(ROOT, '.workbuddy', 'report_bmap.txt'), 'w').write('ok')

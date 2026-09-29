# -*- coding: utf-8 -*-
"""检验 buildings.txt 坐标是否是「整体平移」或「旧版地图」坐标。

思路：
 A) 用 positions.txt 当"真值坐标表"（它与 provinces.bmp 99.69% 吻合）。
    对 buildings.txt 里每个省，取其 positions 坐标 (px, pz)，与建筑坐标 (bx, bz) 求差 (dx,dz)。
    若所有省 dx/dz 近似相同 → 整体平移。
 B) 若 dx/dz 随位置变化 → 可能是缩放（旧地图 5632x2048 → 新 4096x2048）。
"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_bmap2.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

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
        bp[int(f[0])].append((float(f[2]), float(f[4])))
    except ValueError:
        pass

P('=== A. 建筑坐标 - positions 坐标（按省取建筑均值）===')
recs = []
for pid, lst in bp.items():
    if pid not in pos:
        continue
    ar = np.array(lst)
    bx, bz = ar[:, 0].mean(), ar[:, 1].mean()
    px, pz = pos[pid]
    recs.append((pid, bx, bz, px, pz, bx - px, bz - pz))
P(f'   可用省 {len(recs):,}')
d = np.array([(q[5], q[6]) for q in recs])
P(f'   dx = bx-px:  mean={d[:,0].mean():+9.2f}  std={d[:,0].std():8.2f}  min={d[:,0].min():+9.2f}  max={d[:,0].max():+9.2f}')
P(f'   dz = bz-pz:  mean={d[:,1].mean():+9.2f}  std={d[:,1].std():8.2f}  min={d[:,1].min():+9.2f}  max={d[:,1].max():+9.2f}')
P('   前 25 个省的明细:')
P(f'{"pid":<8}{"bx":>9}{"bz":>9}{"px":>9}{"pz":>9}{"dx":>9}{"dz":>9}')
for (pid, bx, bz, px, pz, dx, dz) in recs[:25]:
    P(f'{pid:<8}{bx:>9.1f}{bz:>9.1f}{px:>9.1f}{pz:>9.1f}{dx:>+9.1f}{dz:>+9.1f}')

# 试拟合 dx,dz 是否与 px,pz 线性相关（缩放）
PX = np.array([q[3] for q in recs]); PZ = np.array([q[4] for q in recs])
BX = np.array([q[1] for q in recs]); BZ = np.array([q[2] for q in recs])
P('')
P('=== B. 线性拟合 bx = a*px + c ===')
A1 = np.polyfit(PX, BX, 1)
P(f'   bx = {A1[0]:.6f} * px + {A1[1]:+.3f}   （斜率近 1 且截距近 0 = 同一坐标系）')
r = BX - np.polyval(A1, PX)
P(f'   残差 std={r.std():.2f}  max|r|={np.abs(r).max():.2f}')
A2 = np.polyfit(PZ, BZ, 1)
P(f'   bz = {A2[0]:.6f} * pz + {A2[1]:+.3f}')

P('')
P('=== C. 试换轴：bz vs px / bx vs pz ===')
A3 = np.polyfit(PZ, BX, 1)
P(f'   bx = {A3[0]:.6f} * pz + {A3[1]:+.3f}  残差std={np.std(BX-np.polyval(A3,PZ)):.2f}')
A4 = np.polyfit(PX, BZ, 1)
P(f'   bz = {A4[0]:.6f} * px + {A4[1]:+.3f}  残差std={np.std(BZ-np.polyval(A4,PX)):.2f}')

P('')
P('=== D. 常数比例检验（旧图 5632 宽 → 新图 4096 宽，比例=0.7273）===')
for k in (0.72727, 1.0, 0.5, 0.75):
    P(f'   k={k:.5f}: bx/px 均值={np.mean(BX/PX):.5f}  bz/pz 均值={np.mean(BZ/PZ):.5f}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

# -*- coding: utf-8 -*-
"""标定 HOI4 buildings.txt 世界坐标 (x,z) 与地图像素 (col,row) 的关系。

已知：MOD positions.txt 用的是地图像素坐标（99.69% 命中 provinces.bmp）。
若 HOI4 引擎读取 buildings.txt 时也用同一套坐标，那 MOD 的 buildings.txt 应该也能命中。
既然不命中（0%），说明 buildings.txt 的 x/z 是「世界坐标」，与像素坐标存在线性映射。

HOI4 已知公式（社区标定）：
    x_world = (col - W/2) * scale
    z_world = (row - H/2) * scale     其中 scale 与地图尺寸相关
反解：col = x_world/scale + W/2

用 MOD 的 positions.txt（像素坐标真值）与 MOD 的 buildings.txt（世界坐标）联立，
对同一个省求 scale。
"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_worldmap.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

# 用 position 的 y 列反查：positions y=9.500 恒定。heightmap 和 y 无关。
# 所以唯一线索是：同一省的 buildings 的 x/z 均值 vs positions 的 x/z。
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

P('=== A. 同一省：buildings 坐标均值 vs positions 坐标 ===')
# 挑几个省看是否有线性关系
recs = []
for pid, lst in bp.items():
    if pid not in pos:
        continue
    ar = np.array(lst)
    recs.append((pid, ar[:, 0].mean(), ar[:, 1].mean(), pos[pid][0], pos[pid][1]))
P(f'   省数 {len(recs)}')

bx = np.array([q[1] for q in recs]); bz = np.array([q[2] for q in recs])
px = np.array([q[3] for q in recs]); pz = np.array([q[4] for q in recs])

P('')
P('=== B. 全量回归 bx = a*px + b ===')
for name, X, Y in (('bx = a*px + b', px, bx), ('bz = a*pz + b', pz, bz),
                   ('bx = a*pz + b', pz, bx), ('bz = a*px + b', px, bz)):
    A = np.polyfit(X, Y, 1)
    resid = Y - np.polyval(A, X)
    P(f'   {name:<18} a={A[0]:>+12.6f}  b={A[1]:>+12.3f}   |残差|mean={np.abs(resid).mean():9.2f}  std={resid.std():9.2f}')

P('')
P('=== C. 试 HOI4 世界坐标公式： x_world = (col - W/2)*s, z_world = (row - H/2)*s ===')
Wm, Hm = 4096, 2048
for s in (0.5, 1.0, 1.5, 2.0, 0.25, 0.75):
    xw = (px - Wm / 2) * s
    zw = (pz - Hm / 2) * s
    rx = bx - xw
    rz = bz - zw
    P(f'   s={s:<5} 残差 x: mean={rx.mean():+10.2f} std={rx.std():9.2f} | 残差 z: mean={rz.mean():+10.2f} std={rz.std():9.2f}')

P('')
P('=== D. 直接看比值 bx/px, bz/pz（若为常数即线性过原点）===')
P(f'   bx/px: mean={np.mean(bx/px):.6f}  std={np.std(bx/px):.6f}  中位={np.median(bx/px):.6f}')
P(f'   bz/pz: mean={np.mean(bz/pz):.6f}  std={np.std(bz/pz):.6f}  中位={np.median(bz/pz):.6f}')
P(f'   bx 范围 {bx.min():.1f}~{bx.max():.1f}   px 范围 {px.min():.1f}~{px.max():.1f}')
P(f'   bz 范围 {bz.min():.1f}~{bz.max():.1f}   pz 范围 {pz.min():.1f}~{pz.max():.1f}')

P('')
P('=== E. 前 20 省明细 ===')
P(f'{"pid":<8}{"bx":>10}{"bz":>10}{"px":>10}{"pz":>10}{"bx/px":>9}{"bz/pz":>9}')
for (pid, bxx, bzz, pxx, pzz) in recs[:20]:
    P(f'{pid:<8}{bxx:>10.1f}{bzz:>10.1f}{pxx:>10.1f}{pzz:>10.1f}{bxx/pxx:>9.4f}{bzz/pzz:>9.4f}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

# -*- coding: utf-8 -*-
"""1) 用原版重新标定 buildings.txt 高程公式；2) 查本项目高度图调色板是否恒等；3) 定位悬浮建筑的分布。"""
import struct, os, collections, datetime
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
VAN = r'C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV'
REP = os.path.join(ROOT, '.workbuddy', 'report_buildings_diag2.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))


def read_idx(p):
    raw = open(p, 'rb').read()
    off = struct.unpack_from('<I', raw, 10)[0]
    w, h = struct.unpack_from('<ii', raw, 18)
    dib = struct.unpack_from('<I', raw, 14)[0]
    bpp = struct.unpack_from('<HH', raw, 26)[1]
    cu = struct.unpack_from('<I', raw, 46)[0]
    po = 14 + dib
    n = cu or (off - 14 - dib) // 4 or 256
    pal = [tuple(raw[po + i * 4: po + i * 4 + 3][::-1]) for i in range(n)]
    a = np.frombuffer(raw[off:off + w * h], dtype=np.uint8).reshape(h, w)
    return a[::-1], pal, (len(raw), off, w, h, bpp, cu)


def load_b(p):
    out = []
    for ln in open(p, encoding='utf-8', errors='replace'):
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        f = s.split(';')
        if len(f) < 6:
            continue
        try:
            out.append((int(f[0]), f[1], float(f[2]), float(f[3]), float(f[4])))
        except ValueError:
            pass
    return out


def sample(hm, x, z):
    H, W = hm.shape
    fy = H - 1 - z
    fx = x
    if fy < 0 or fy > H - 2 or fx < 0 or fx > W - 2:
        return None
    y0 = int(fy); x0 = int(fx)
    dy = fy - y0; dx = fx - x0
    return (hm[y0, x0] * (1 - dx) + hm[y0, x0 + 1] * dx) * (1 - dy) + \
           (hm[y0 + 1, x0] * (1 - dx) + hm[y0 + 1, x0 + 1] * dx) * dy


def fit(hm, recs, tag):
    hs, ys = [], []
    for (_p, _t, x, y, z) in recs:
        h = sample(hm, x, z)
        if h is None:
            continue
        hs.append(h); ys.append(y)
    hs = np.array(hs); ys = np.array(ys)
    A, B = np.polyfit(hs, ys, 1)
    pred = A * hs + B
    r = ys - pred
    P(f'--- {tag} ---')
    P(f'   样本 {len(hs):,}   h 范围 {hs.min():.0f}..{hs.max():.0f}   y 范围 {ys.min():.3f}..{ys.max():.3f}')
    P(f'   最小二乘拟合  y = {A:.8f} * h + {B:.6f}      R^2 = {1 - r.var()/ys.var():.6f}')
    P(f'   mean|r| = {np.abs(r).mean():.4f}   p95|r| = {np.percentile(np.abs(r),95):.4f}   max|r| = {np.abs(r).max():.3f}')
    for th in (0.5, 1.0, 2.0, 5.0, 20.0):
        P(f'   |r| <= {th:<5} = {100.0*np.mean(np.abs(r) <= th):6.2f}%   超出 {int((np.abs(r) > th).sum()):,} 条')
    return A, B, r, hs, ys


P('=== A. 原版标定（检验公式本身）===')
vhm_p = os.path.join(VAN, 'map', 'heightmap.bmp')
vbp = os.path.join(VAN, 'map', 'buildings.txt')
if os.path.exists(vhm_p) and os.path.exists(vbp):
    vhm, vpal, vmeta = read_idx(vhm_p)
    P(f'   vanilla heightmap {vmeta[0]:,} B off={vmeta[1]} {vmeta[2]}x{vmeta[3]} bpp={vmeta[4]} clrUsed={vmeta[5]}')
    P(f'   调色板前 4 项 {vpal[:4]}   恒等灰度 = {all(vpal[i] == (i, i, i) for i in range(len(vpal))) if vpal else "N/A"}')
    vrecs = load_b(vbp)
    P(f'   vanilla buildings.txt {len(vrecs):,} 条')
    fit(vhm, vrecs, 'VANILLA heightmap + VANILLA buildings')
else:
    P(f'   找不到原版文件 {vhm_p} / {vbp}')

P('')
P('=== B. 本项目高度图调色板 ===')
for n in ['heightmap.bmp', 'heightmap_01.bmp']:
    p = os.path.join(MAP, n)
    hm, pal, meta = read_idx(p)
    ident = all(pal[i] == (i, i, i) for i in range(min(len(pal), 256))) if pal else False
    P(f'   {n}: {meta[0]:,} B off={meta[1]} {meta[2]}x{meta[3]} bpp={meta[4]} clrUsed={meta[5]} palN={len(pal)}')
    P(f'      恒等灰度 = {ident}')
    P(f'      调色板前 6 项 {pal[:6]} ... 第 200..205 项 {pal[200:206] if len(pal) > 205 else "N/A"}')
    idx_pal = np.array([pal[v][0] if v < len(pal) else 0 for v in range(256)])
    P(f'      像素索引 -> 调色板灰度 的差异(=索引与灰度不同值的索引个数) = '
      f'{int((idx_pal != np.arange(256)).sum())}')

P('')
P('=== C. 本项目 buildings.txt 的离群点 ===')
hm, pal, meta = read_idx(os.path.join(MAP, 'heightmap.bmp'))
recs = load_b(os.path.join(MAP, 'buildings.txt'))
A, B, r, hs, ys = fit(hm, recs, 'MOD heightmap.bmp + MOD buildings.txt')

pred = ys - r
rec_ok = [(_p, _t, x, y, z, h, p_, rr) for (_p, _t, x, y, z), h, p_, rr in zip(recs, hs, pred, r)]
bad = [q for q in rec_ok if abs(q[7]) > 0.5]
P(f'   |r| > 0.5 的 {len(bad):,} 条   其中正残差(悬空){sum(1 for q in bad if q[7] > 0)} 条，'
  f'负残差(陷地){sum(1 for q in bad if q[7] < 0)} 条')
P(f'   残差绝对值 分位: p50={np.percentile(np.abs(r),50):.3f} p90={np.percentile(np.abs(r),90):.3f} '
  f'p99={np.percentile(np.abs(r),99):.3f} p99.9={np.percentile(np.abs(r),99.9):.3f} max={np.abs(r).max():.3f}')

P('   残差最大的 20 条:')
for q in sorted(rec_ok, key=lambda q: -abs(q[7]))[:20]:
    P(f'      省{q[0]:<6} {q[1]:<22} x={q[2]:8.2f} z={q[4]:8.2f}  y={q[3]:8.3f}  '
      f'h={q[5]:6.1f}  预测={q[6]:8.3f}  残差={q[7]:+8.3f}')

P('   按建筑类型统计 |r|>0.5 的占比:')
by = collections.Counter()
tot = collections.Counter()
for q in rec_ok:
    tot[q[1]] += 1
    if abs(q[7]) > 0.5:
        by[q[1]] += 1
for t, c in sorted(tot.items(), key=lambda kv: -by[kv[0]]):
    P(f'      {t:<24} {by[t]:>6}/{c:<6}  {100.0*by[t]/c:6.2f}%')

P('   离群点空间分布（100 像素一格，取前 12 格）:')
grid = collections.Counter()
for q in bad:
    grid[(int(q[2] // 100), int(q[4] // 100))] += 1
for (gx, gy), c in grid.most_common(12):
    P(f'      x={gx*100:<5} z={gy*100:<5}  离群 {c} 条   图元坐标 ({gx*100+50},{gy*100+50})')

P('')
P('=== D. 文件时间 ===')
for n in ['buildings.txt', 'buildings_01.txt', 'heightmap.bmp', 'heightmap_01.bmp', 'positions.txt', 'positions_fixed.txt']:
    p = os.path.join(MAP, n)
    if os.path.exists(p):
        P(f'   {n:22s} {os.path.getsize(p):>10,} B  '
          f'{datetime.datetime.fromtimestamp(os.path.getmtime(p)):%Y-%m-%d %H:%M:%S}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

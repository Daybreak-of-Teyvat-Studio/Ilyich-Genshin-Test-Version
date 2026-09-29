# -*- coding: utf-8 -*-
"""定位建筑悬空/陷地：对比两张高度图，并按省份海陆拆开统计建筑残差。"""
import struct, os, csv, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_buildings_diag3.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

def read_idx(p):
    raw = open(p, 'rb').read()
    off = struct.unpack_from('<I', raw, 10)[0]
    w, h = struct.unpack_from('<ii', raw, 18)
    a = np.frombuffer(raw[off:off + w * h], dtype=np.uint8).reshape(h, w)
    return a[::-1]

hm_now = read_idx(os.path.join(MAP, 'heightmap.bmp'))
hm_01 = read_idx(os.path.join(MAP, 'heightmap_01.bmp'))
H, W = hm_now.shape
P(f'=== A. 两张高度图对比 ===  尺寸 {W}x{H}')

d = hm_now.astype(int) - hm_01.astype(int)
nz = d != 0
P(f'   有差异的像素 {int(nz.sum()):,} / {d.size:,} = {100.0*nz.mean():.3f}%')
P(f'   差值 分布: 上调(now>01) {int((d > 0).sum()):,}   下调 {int((d < 0).sum()):,}')
if nz.any():
    P(f'   差值幅度: mean={d[nz].mean():+.3f}  min={d.min():+d}  max={d.max():+d}')
    P(f'   差值绝对值 分位: p50={np.percentile(np.abs(d[nz]),50):.1f} p90={np.percentile(np.abs(d[nz]),90):.1f} '
      f'p99={np.percentile(np.abs(d[nz]),99):.1f} max={np.abs(d).max()}')
    ann = collections.Counter(d[nz].tolist())
    P(f'   最常见的差值: {ann.most_common(12)}')
    # 差异聚集区
    g = collections.Counter()
    ys, xs = np.where(nz)
    for yy, xx in zip(ys[:: max(1, len(ys) // 40000)], xs[:: max(1, len(xs) // 40000)]):
        g[(xx // 256, yy // 256)] += 1
    P('   差异最密的区块（256px 格）:')
    for (gx, gy), c in g.most_common(10):
        sub = d[gy * 256:(gy + 1) * 256, gx * 256:(gx + 1) * 256]
        P(f'      x={gx*256:<5} z={(H-1-(gy+1)*256):<5} 差异像素 {c}  该格差值 min={sub.min():+d} max={sub.max():+d}')

P('')
P('   (2269,1392) 采样:  now={} 01={}'.format(hm_now[1392, 2269], hm_01[1392, 2269]))
P('   (2260,1380) 附近 8x8 now 均值={:.1f} 01 均值={:.1f}'.format(
    hm_now[1376:1384, 2256:2264].mean(), hm_01[1376:1384, 2256:2264].mean()))

# ---- 省份海陆 ----
sea = set()
defp = os.path.join(MAP, 'definition.csv')
if os.path.exists(defp):
    with open(defp, encoding='utf-8', errors='replace') as f:
        for ln in f:
            f2 = ln.strip().split(';')
            if len(f2) >= 5 and f2[4] in ('ocean', 'lake'):
                sea.add(int(f2[0]))
P('')
P(f'=== B. definition.csv: 海/湖省份 {len(sea):,} 个 ===')

A, B = 0.09786518, 0.259962
def sample(hm, x, z):
    fy = H - 1 - z
    fx = x
    if fy < 0 or fy > H - 2 or fx < 0 or fx > W - 2:
        return None
    y0 = int(fy); x0 = int(fx)
    dy = fy - y0; dx = fx - x0
    return (hm[y0, x0] * (1 - dx) + hm[y0, x0 + 1] * dx) * (1 - dy) + \
           (hm[y0 + 1, x0] * (1 - dx) + hm[y0 + 1, x0 + 1] * dx) * dy

recs = []
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    s = ln.strip()
    if not s or s.startswith('#'):
        continue
    f = s.split(';')
    if len(f) < 6:
        continue
    try:
        recs.append((int(f[0]), f[1], float(f[2]), float(f[3]), float(f[4])))
    except ValueError:
        pass

def stats(sel, hmsel, tag):
    r = []
    for (_p, _t, x, y, z) in recs:
        h = sample(hmsel, x, z)
        if h is None:
            continue
        if sel(_p):
            r.append((y - (A * h + B), h, x, z, y, _p, _t))
    if not r:
        P(f'   {tag}: 无样本')
        return r
    rr = np.array([q[0] for q in r])
    P(f'   {tag}: {len(r):,} 条   mean|r|={np.abs(rr).mean():.4f}  正残差(悬空)={int((rr>0.5).sum()):,}  '
      f'负残差(陷地)={int((rr<-0.5).sum()):,}')
    for th in (0.5, 1.0, 2.0, 5.0):
        P(f'      |r|>{th}: {int((np.abs(rr)>th).sum()):,}')
    return r

P('')
P('=== C. 按海陆拆开 ===')
land = stats(lambda p: p not in sea, hm_now, '陆地省份 · heightmap.bmp(现行)')
land01 = stats(lambda p: p not in sea, hm_01, '陆地省份 · heightmap_01.bmp(11:58)')
seab = stats(lambda p: p in sea, hm_now, '海域省份 · heightmap.bmp(现行)')

P('')
P('=== D. 陆地建筑里残差最大的 25 条（对现行高度图）===')
for q in sorted(land, key=lambda q: -abs(q[0]))[:25]:
    P(f'   省{q[5]:<6} {q[6]:<26} x={q[2]:8.2f} z={q[3]:8.2f} y={q[4]:8.3f} h={q[1]:6.1f} '
      f'应为={A*q[1]+B:7.3f} 残差={q[0]:+7.3f}')

P('')
P('=== E. 陆地建筑里"悬空"(r>0.5) 的类型分布 ===')
by = collections.Counter(); tot = collections.Counter()
for q in land:
    tot[q[6]] += 1
    if q[0] > 0.5:
        by[q[6]] += 1
for t, c in sorted(tot.items(), key=lambda kv: -by[kv[0]])[:14]:
    P(f'   {t:<28} {by[t]:>5}/{c:<6} {100.0*by[t]/c:6.2f}%')

P('')
P('=== F. 悬空建筑的空间聚集（128px 格）===')
g = collections.Counter()
for q in land:
    if q[0] > 0.5:
        g[(int(q[2] // 128), int((H - 1 - q[3]) // 128))] += 1
for (gx, gy), c in g.most_common(15):
    P(f'   图元 x={gx*128+64:<6} z={H-1-(gy*128+64):<6} 悬空 {c} 条')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

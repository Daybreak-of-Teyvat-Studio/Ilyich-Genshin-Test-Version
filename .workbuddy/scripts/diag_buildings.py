# -*- coding: utf-8 -*-
"""诊断 buildings.txt 的高程列与当前高度图的吻合度。"""
import struct, os, collections
import numpy as np

MAP = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map'
REP = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_buildings_diag.txt'

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

def read8(p):
    raw = open(p, 'rb').read()
    off = struct.unpack_from('<I', raw, 10)[0]
    w, h = struct.unpack_from('<ii', raw, 18)
    bpp = struct.unpack_from('<HH', raw, 26)[1]
    cu = struct.unpack_from('<I', raw, 46)[0]
    a = np.frombuffer(raw[off:off + w * h], dtype=np.uint8).reshape(h, w)
    return a[::-1].astype(np.float64), (len(raw), off, w, h, bpp, cu)

HMS = {}
for name in ['heightmap.bmp', 'heightmap_01.bmp']:
    p = os.path.join(MAP, name)
    if os.path.exists(p):
        arr, meta = read8(p)
        HMS[name] = arr
        P(f'{name:22s} size={meta[0]:,} off={meta[1]} {meta[2]}x{meta[3]} bpp={meta[4]} clrUsed={meta[5]}')
        P(f'    min={arr.min():.0f} max={arr.max():.0f} mean={arr.mean():.2f} unique={len(np.unique(arr))}')
        P(f'    <96 的像素 {int((arr < 96).sum()):,}   >=96 的 {int((arr >= 96).sum()):,}')

# ---- buildings.txt 结构 ----
bp = os.path.join(MAP, 'buildings.txt')
lines = [ln.rstrip('\n') for ln in open(bp, encoding='utf-8', errors='replace')]
P('')
P(f'=== {bp} 共 {len(lines)} 行 ===')
for ln in lines[:6]:
    P('   ' + ln)

recs = []
nfield = collections.Counter()
for ln in lines:
    s = ln.strip()
    if not s or s.startswith('#'):
        continue
    f = s.split(';')
    nfield[len(f)] += 1
    if len(f) >= 5:
        try:
            recs.append((int(f[0]), f[1], float(f[2]), float(f[3]), float(f[4]), int(float(f[5])) if len(f) > 5 and f[5].strip() else 0))
        except ValueError:
            pass
P(f'   字段数分布 {dict(nfield)}   可解析记录 {len(recs):,} 条')
P('   第 5 列(索引4) 即高程 y 的分布：',
  f'min={min(r[4] for r in recs):.3f} max={max(r[4] for r in recs):.3f} '
  f'mean={np.mean([r[4] for r in recs]):.3f} unique={len(set(round(r[4],3) for r in recs))}')

A = 0.09786518
B = 0.259962

def sample(hm, x, z):
    H, W = hm.shape
    fy = H - 1 - z
    fx = x
    if fy < 0 or fy > H - 2 or fx < 0 or fx > W - 2:
        return None
    y0 = int(np.floor(fy)); x0 = int(np.floor(fx))
    dy = fy - y0; dx = fx - x0
    h00 = hm[y0, x0]; h01 = hm[y0, x0 + 1]; h10 = hm[y0 + 1, x0]; h11 = hm[y0 + 1, x0 + 1]
    return (h00 * (1 - dx) + h01 * dx) * (1 - dy) + (h10 * (1 - dx) + h11 * dx) * dy

for name, hm in HMS.items():
    P('')
    P(f'=== 与 {name} 比对的残差（y - (A*h+B)） ===')
    res = []
    for (_p, _t, x, y, z, _rot) in recs:
        h = sample(hm, x, z)
        if h is None:
            continue
        res.append(y - (A * h + B))
    r = np.array(res)
    P(f'   样本 {len(r):,}   mean={r.mean():.3f}   mean|r|={np.abs(r).mean():.4f}   '
      f'p50|r|={np.median(np.abs(r)):.3f}   p95|r|={np.percentile(np.abs(r),95):.3f}')
    for th in (0.5, 1.0, 2.0, 5.0):
        P(f'   |r| <= {th:<4} 的比例 = {100.0*np.mean(np.abs(r) <= th):.2f}%   '
          f'超出 {int(np.sum(np.abs(r) > th)):,} 条')
    P(f'   相关系数 corr(y, A*h+B) = {np.corrcoef(r + (A*np.array([sample(hm,b[2],b[4]) for b in recs]), ), ) if False else np.corrcoef([b[3] for b in recs if sample(hm,b[2],b[4]) is not None], [A*sample(hm,b[2],b[4])+B for b in recs if sample(hm,b[2],b[4]) is not None])[0,1]:.4f}')

# ---- 高度图是否被改过：与 13:47 的备份对比（若有）----
P('')
P('=== 高度图文件时间 ===')
for n in sorted(os.listdir(MAP)):
    if n.startswith('heightmap') and n.endswith('.bmp'):
        p = os.path.join(MAP, n)
        import datetime
        P(f'   {n:26s} {os.path.getsize(p):,} B   {datetime.datetime.fromtimestamp(os.path.getmtime(p)):%Y-%m-%d %H:%M:%S}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

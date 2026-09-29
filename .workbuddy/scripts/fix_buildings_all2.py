# -*- coding: utf-8 -*-
"""修复 2/2（修正版）：全量核对 buildings.txt 第 4 列高程。
★关键：采样映射是 row = z, col = x（与 positions.txt 一致），不是 H-1-z。
规则：
  - floating_harbor 保持原 y
  - 其余按 y = 0.09786518*h + 0.259962 重算，仅当 |Δ|>0.005 才改
产物 -> .workbuddy/buildings_fixall2.txt"""
import struct, os, hashlib, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
SRC = os.path.join(MAP, 'buildings.txt')
OUT = os.path.join(ROOT, '.workbuddy', 'buildings_fixall2.txt')
BK = os.path.join(ROOT, '.workbuddy', 'backup_20260924_buildings_all2')
REP = os.path.join(ROOT, '.workbuddy', 'report_buildings_fixall2.txt')
os.makedirs(BK, exist_ok=True)

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

A, B = 0.09786518, 0.259962

raw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
hoff = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
hm = np.frombuffer(raw, dtype=np.uint8, offset=hoff)[:W * H].reshape(H, W)
P(f'heightmap.bmp {W}x{H}  采样映射 row=z, col=x')

def bilinear(x, z):
    """双线性采样，row=z col=x。"""
    r = z; c = x
    r0 = int(r); c0 = int(c)
    if r0 < 0 or r0 > H - 2 or c0 < 0 or c0 > W - 2:
        return None
    dr = r - r0; dc = c - c0
    return (hm[r0, c0] * (1 - dc) + hm[r0, c0 + 1] * dc) * (1 - dr) + \
           (hm[r0 + 1, c0] * (1 - dc) + hm[r0 + 1, c0 + 1] * dc) * dr

data = open(SRC, 'rb').read()
P(f'原文件 {len(data):,} B  md5={hashlib.md5(data).hexdigest()}')
open(os.path.join(BK, 'buildings.txt'), 'wb').write(data)
P(f'已备份 -> {os.path.join(BK, "buildings.txt")}')

lines = data.split(b'\n')
stat = collections.Counter()
delta = []
moved = []
out = []
for ln in lines:
    core = ln[:-1] if ln.endswith(b'\r') else ln
    tail = ln[len(core):]
    if not core.strip() or core.lstrip().startswith(b'#'):
        out.append(ln); stat['非数据行'] += 1; continue
    f = core.split(b';')
    if len(f) < 6:
        out.append(ln); stat['字段不足'] += 1; continue
    try:
        typ = f[1].decode('ascii')
        x = float(f[2]); y0 = float(f[3]); z = float(f[4])
    except (ValueError, UnicodeDecodeError):
        out.append(ln); stat['无法解析'] += 1; continue
    h = bilinear(x, z)
    if h is None:
        out.append(ln); stat['采样越界'] += 1; continue
    if typ == 'floating_harbor':
        newy = y0; stat['floating_harbor保持'] += 1
    else:
        newy = A * h + B
        stat['陆地重算'] += 1
        d = newy - y0
        delta.append(d)
        if abs(d) > 0.005:
            moved.append((typ, x, z, y0, newy, h, d))
        else:
            newy = y0   # 不必要就不改，保持原样
    f[3] = f'{newy:.2f}'.encode('ascii')
    out.append(b';'.join(f) + tail)

new_data = b'\n'.join(out)
open(OUT, 'wb').write(new_data)

P('')
P(f'新文件 {len(new_data):,} B  md5={hashlib.md5(new_data).hexdigest()}  字节差 {len(new_data)-len(data):+d}')
P('')
P('=== 处理统计 ===')
for k, v in stat.items():
    P(f'   {k:<22} {v:,}')

d = np.array(delta)
P('')
P('=== 残差（原文件 vs 高度图重算值）===')
P(f'   样本 {len(d):,}  mean={d.mean():+.4f}  mean|Δ|={np.abs(d).mean():.4f}  min={d.min():+.3f}  max={d.max():+.3f}')
for th in (0.005, 0.5, 1.0, 2.0, 5.0):
    P(f'   |Δ|>{th:<6} {int((np.abs(d)>th).sum()):,}')

P('')
P('=== 逐行字节校验 ===')
ol = data.split(b'\n'); nl = new_data.split(b'\n')
P(f'   行数 {len(ol):,} vs {len(nl):,}  一致={len(ol)==len(nl)}')
badpre = badsuf = 0
for a, b in zip(ol, nl):
    fa = a[:(len(a)-1 if a.endswith(b"\r") else len(a))].split(b';')
    fb = b[:(len(b)-1 if b.endswith(b"\r") else len(b))].split(b';')
    if len(fa) < 6 or len(fb) < 6:
        continue
    if fa[:3] != fb[:3]: badpre += 1
    if fa[4:] != fb[4:]: badsuf += 1
P(f'   前 3 列不一致={badpre}   第 5 列及以后不一致={badsuf}')
P(f'   实际变化行数 = {sum(1 for a,b in zip(ol,nl) if a!=b):,}  （应为 {len(moved):,}）')

P('')
P('=== |Δ| 最大的 25 条 ===')
for (t, x, z, y0, y1, h, dd) in sorted(moved, key=lambda q: -abs(q[6]))[:25]:
    P(f'   {t:<30} x={x:8.2f} z={z:8.2f} h={h:6.1f}  y {y0:7.2f} -> {y1:7.2f}  Δ={dd:+7.3f}')

# 修复后残差
res2 = []
for ln in open(OUT, encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        t = f[1]; x = float(f[2]); y = float(f[3]); z = float(f[4])
    except ValueError:
        continue
    if t == 'floating_harbor':
        continue
    h = bilinear(x, z)
    if h is None:
        continue
    res2.append(y - (A * h + B))
r2 = np.array(res2)
P('')
P(f'=== 修复后残差 ===  {len(r2):,} 条  mean|r|={np.abs(r2).mean():.6f}  max|r|={np.abs(r2).max():.6f}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

# -*- coding: utf-8 -*-
"""按现行 heightmap.bmp 重算 buildings.txt 的陆地建筑高程（按字节处理，行尾原样保留）。
规则：floating_harbor 与采样点在水下(h<96)的一律保持原 y（水面建筑不重算）；
其余按 y = 0.09786518*h + 0.259962 重算，h 为 row=H-1-z、col=x 的双线性采样。
除第 4 列外，文件其余字节保持原样。"""
import struct, os, hashlib, shutil, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
SRC = os.path.join(MAP, 'buildings.txt')
OUT = os.path.join(ROOT, '.workbuddy', 'buildings_new.txt')
BK = os.path.join(ROOT, '.workbuddy', 'backup_20260924_1625')
REP = os.path.join(ROOT, '.workbuddy', 'report_buildings_fix.txt')
os.makedirs(BK, exist_ok=True)

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

A, B = 0.09786518, 0.259962
LAND_MIN = 96

raw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
hoff = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
hm = np.frombuffer(raw[hoff:hoff + W * H], dtype=np.uint8).reshape(H, W)[::-1]
P(f'高度图 heightmap.bmp  {W}x{H}  off={hoff}  min={hm.min()} max={hm.max()}')


def sample(x, z):
    fy = H - 1 - z
    fx = x
    if fy < 0 or fy > H - 2 or fx < 0 or fx > W - 2:
        return None
    y0 = int(fy); x0 = int(fx)
    dy = fy - y0; dx = fx - x0
    return (hm[y0, x0] * (1 - dx) + hm[y0, x0 + 1] * dx) * (1 - dy) + \
           (hm[y0 + 1, x0] * (1 - dx) + hm[y0 + 1, x0 + 1] * dx) * dy


data = open(SRC, 'rb').read()
P('')
P(f'备份 {os.path.join(BK, "buildings.txt")}')
P(f'原文件 {len(data):,} B  md5={hashlib.md5(data).hexdigest()}  '
  f'CRLF={data.count(b"\\r\\n"):,}  LF={data.count(b"\\n"):,}')
shutil.copy2(SRC, os.path.join(BK, 'buildings.txt'))

lines = data.split(b'\n')
stat = collections.Counter()
delta = []
changed_pos = []
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
    h = sample(x, z)
    if h is None:
        out.append(ln); stat['采样越界'] += 1; continue
    if typ == 'floating_harbor':
        newy = y0; stat['floating_harbor 保持水面'] += 1
    elif h < LAND_MIN:
        newy = y0; stat['水下点保持原值'] += 1
    else:
        newy = A * h + B
        stat['陆地重算'] += 1
        d = newy - y0
        delta.append(d)
        if abs(d) > 0.5:
            changed_pos.append((x, z, y0, newy, typ, h))
    f[3] = f'{newy:.2f}'.encode('ascii')
    out.append(b';'.join(f) + tail)

new_data = b'\n'.join(out)
open(OUT, 'wb').write(new_data)

P('')
P(f'新文件 {len(new_data):,} B  md5={hashlib.md5(new_data).hexdigest()}  '
  f'CRLF={new_data.count(b"\\r\\n"):,}  LF={new_data.count(b"\\n"):,}')
P('')
P('=== 处理统计 ===')
for k, v in stat.items():
    P(f'   {k:<26} {v:,}')

d = np.array(delta)
P('')
P('=== 重算建筑（陆地）的改动量 ===')
P(f'   重算 {len(d):,} 条   Δ:  mean={d.mean():+.4f}  mean|Δ|={np.abs(d).mean():.4f}  '
  f'min={d.min():+.3f}  max={d.max():+.3f}')
for th in (0.1, 0.5, 1.0, 2.0, 5.0):
    P(f'   |Δ|>{th:<4}: {int((np.abs(d) > th).sum()):,} 条')
P(f'   |Δ|<=0.005 未动: {int((np.abs(d) <= 0.005).sum()):,} 条')

P('')
P('=== 逐行字节校验（只有第 4 列允许不同）===')
ol = data.split(b'\n'); nl = new_data.split(b'\n')
P(f'   行数 原 {len(ol):,} 新 {len(nl):,}  一致={len(ol) == len(nl)}')
badpre = badsuf = badlast = 0
for a, b in zip(ol, nl):
    fa = a[:(len(a) - 1 if a.endswith(b"\r") else len(a))].split(b';')
    fb = b[:(len(b) - 1 if b.endswith(b"\r") else len(b))].split(b';')
    if len(fa) < 6 or len(fb) < 6:
        if a != b:
            badlast += 1
        continue
    if fa[:3] != fb[:3]:
        badpre += 1
    if fa[4:] != fb[4:]:
        badsuf += 1
P(f'   前 3 列不一致 = {badpre}   第 5 列及以后不一致 = {badsuf}   非数据行被改 = {badlast}')
P(f'   行尾 CRLF 数 原 {data.count(bytes([13, 10])):,} 新 {new_data.count(bytes([13, 10])):,}')

P('')
P('=== 影响最重的区域（128px 格）===')
g = collections.Counter()
for (x, z, y0, y1, typ, h) in changed_pos:
    g[(int(x // 128), int((H - 1 - z) // 128))] += 1
for (gx, gy), c in g.most_common(12):
    P(f'   图元 x≈{gx*128+64:<6} z≈{H-1-(gy*128+64):<6}  改动 {c} 条')

P('')
P('=== |Δ| 最大的 25 条 ===')
for (x, z, y0, y1, typ, h) in sorted(changed_pos, key=lambda t: -abs(t[3] - t[2]))[:25]:
    P(f'   {typ:<30} x={x:8.2f} z={z:8.2f} h={h:6.1f}  y {y0:7.2f} -> {y1:7.2f}  Δ={y1-y0:+7.3f}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

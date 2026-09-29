# -*- coding: utf-8 -*-
"""按现行 heightmap.bmp 重算 positions.txt 里省份位置的高度。
规则：h>=96（陆地）→ y = 0.09786518*h + 0.259962；h<96（海域）→ 保持原值（水面，不沉到海底）。
只改 position 行里的第 2 个数，其余字节原样保留。"""
import struct, os, re, hashlib, shutil, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
SRC = os.path.join(MAP, 'positions.txt')
OUT = os.path.join(ROOT, '.workbuddy', 'positions_new.txt')
BK = os.path.join(ROOT, '.workbuddy', 'backup_20260924_1640')
REP = os.path.join(ROOT, '.workbuddy', 'report_positions_fix.txt')
os.makedirs(BK, exist_ok=True)

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

A, B = 0.09786518, 0.259962
LAND_MIN = 96

raw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
T = np.frombuffer(raw[o:o + W * H], dtype=np.uint8).reshape(H, W)[::-1]


def sample(x, z):
    fy = H - 1 - z; fx = x
    if fy < 0 or fy > H - 2 or fx < 0 or fx > W - 2:
        return None
    y0 = int(fy); x0 = int(fx); dy = fy - y0; dx = fx - x0
    return (T[y0, x0] * (1 - dx) + T[y0, x0 + 1] * dx) * (1 - dy) + \
           (T[y0 + 1, x0] * (1 - dx) + T[y0 + 1, x0 + 1] * dx) * dy


data = open(SRC, 'rb').read()
P(f'原 positions.txt {len(data):,} B  md5={hashlib.md5(data).hexdigest()}')
shutil.copy2(SRC, os.path.join(BK, 'positions.txt'))

blk = re.compile(rb'^(\d+)=\{$')
pos = re.compile(rb'^([ \t]*)([\d.]+)([ \t]+)([\d.]+)([ \t]+)([\d.]+)([ \t]*)$')

lines = data.split(b'\n')
out = []
cur = None
newy = None
stat = collections.Counter()
deltas = []
for ln in lines:
    body = ln[:-1] if ln.endswith(b'\r') else ln
    tail = ln[len(body):]
    m = blk.match(body)
    if m:
        cur = int(m.group(1)); newy = None; stat['省份块'] += 1
        out.append(ln); continue
    if cur is not None:
        pm = pos.match(body)
        if pm:
            x, y0, z = float(pm.group(2)), float(pm.group(4)), float(pm.group(6))
            if newy is None:
                h = sample(x, z)
                if h is None:
                    newy = y0; stat['采样越界保持原值'] += 1
                elif h < LAND_MIN:
                    newy = y0; stat['海域保持水面'] += 1
                else:
                    newy = A * h + B
                    stat['陆地重算'] += 1
                    deltas.append(newy - y0)
            s = f'{newy:.3f}'.encode('ascii')
            out.append(pm.group(1) + pm.group(2) + pm.group(3) + s + pm.group(5) + pm.group(6) + pm.group(7) + tail)
            continue
    out.append(ln)

new_data = b'\n'.join(out)
open(OUT, 'wb').write(new_data)

P('')
P(f'新 positions.txt {len(new_data):,} B  md5={hashlib.md5(new_data).hexdigest()}')
P('')
P('=== 处理统计 ===')
for k, v in stat.items():
    P(f'   {k:<20} {v:,}')
d = np.array(deltas)
P('')
P(f'=== 陆地省份高度改动 {len(d):,} 个 ===')
P(f'   Δ: mean={d.mean():+.3f}  mean|Δ|={np.abs(d).mean():.4f}  min={d.min():+.3f}  max={d.max():+.3f}')
for th in (0.5, 1.0, 2.0, 5.0, 10.0):
    P(f'   |Δ|>{th:<5}: {int((np.abs(d) > th).sum()):,} 个')

P('')
P('=== 逐行校验 ===')
ol = data.split(b'\n'); nl = new_data.split(b'\n')
P(f'   行数 原 {len(ol):,} 新 {len(nl):,} 一致={len(ol) == len(nl)}')
chg = sum(1 for a, b in zip(ol, nl) if a != b)
P(f'   内容不同的行 = {chg:,}')
P(f'   行尾 CRLF 数 原 {data.count(bytes([13,10])):,} 新 {new_data.count(bytes([13,10])):,}')
# 抽查：每行除第 2 个数外必须一致
bad = 0
for a, b in zip(ol, nl):
    fa = a.rstrip(b'\r').split(); fb = b.rstrip(b'\r').split()
    if len(fa) == 3 and len(fb) == 3:
        if fa[0] != fb[0] or fa[2] != fb[2]:
            bad += 1
P(f'   第 1、3 个数或结构被改的行 = {bad}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

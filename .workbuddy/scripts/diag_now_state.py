# -*- coding: utf-8 -*-
"""当前实际状态快照：关键文件时间戳/md5 + buildings.txt 全量残差核查（按类型拆）。"""
import struct, os, re, hashlib, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_now_state.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

A, B = 0.09786518, 0.259962
LAND_MIN = 96

def md5(p):
    try:
        return hashlib.md5(open(p, 'rb').read()).hexdigest()
    except Exception as e:
        return f'ERR {e}'

def mtime(p):
    import time
    try:
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))
    except Exception as e:
        return f'ERR {e}'

P('=== A. 关键文件状态 ===')
for rel in ['map/buildings.txt', 'map/positions.txt', 'map/positions_fixed.txt',
            'map/heightmap.bmp', 'map/heightmap_01.bmp', 'map/terrain.bmp',
            'map/default.map', 'map/trees.bmp', 'map/rivers.bmp',
            'map/cities.bmp', 'map/unitstacks.txt', 'map/supply_nodes.txt']:
    p = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', rel)
    if os.path.exists(p):
        P(f'   {rel:<28} {os.path.getsize(p):>11,} B  mtime={mtime(p)}  md5={md5(p)[:16]}')
    else:
        P(f'   {rel:<28} (不存在)')

# 备份
BK = os.path.join(ROOT, '.workbuddy')
P('')
P('   --- .workbuddy 里我产的候选 ---')
for d in sorted(os.listdir(BK)):
    p = os.path.join(BK, d)
    if os.path.isfile(p) and ('buildings' in d or 'positions' in d):
        P(f'   {d:<36} {os.path.getsize(p):>11,} B  mtime={mtime(p)}')
for d in sorted(os.listdir(BK)):
    p = os.path.join(BK, d)
    if os.path.isdir(p) and d.startswith('backup'):
        for f in sorted(os.listdir(p)):
            if 'buildings' in f or 'positions' in f:
                P(f'   {d}/{f:<30} {os.path.getsize(os.path.join(p, f)):>11,} B  mtime={mtime(os.path.join(p, f))}')

# --- 高度图 ---
raw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
bpp = struct.unpack_from('<H', raw, 28)[0]
hm = np.frombuffer(raw[o:o + W * H], dtype=np.uint8).reshape(H, W)[::-1]
P('')
P(f'=== B. heightmap.bmp ===  {W}x{H}  {bpp}bpp  off={o}  min={hm.min()} max={hm.max()}  '
  f'海面(<=92)像素 {int((hm<=92).sum()):,}  陆地(>=96)像素 {int((hm>=96).sum()):,}')

# --- 地形 ---
traw = open(os.path.join(MAP, 'terrain.bmp'), 'rb').read()
toff = struct.unpack_from('<I', traw, 10)[0]
TW, TH = struct.unpack_from('<ii', traw, 18)
tbpp = struct.unpack_from('<H', traw, 28)[0]
P(f'=== C. terrain.bmp ===  {TW}x{TH}  {tbpp}bpp  off={toff}  尺寸一致={TW==W and TH==H}')

def sample(x, z):
    fy = H - 1 - z
    fx = x
    if fy < 0 or fy > H - 2 or fx < 0 or fx > W - 2:
        return None
    y0 = int(fy); x0 = int(fx)
    dy = fy - y0; dx = fx - x0
    return (hm[y0, x0] * (1 - dx) + hm[y0, x0 + 1] * dx) * (1 - dy) + \
           (hm[y0 + 1, x0] * (1 - dx) + hm[y0 + 1, x0 + 1] * dx) * dy

# --- buildings.txt 全量 ---
src = os.path.join(MAP, 'buildings.txt')
recs = []
bad = 0
for ln in open(src, 'rb').read().split(b'\n'):
    core = ln.rstrip(b'\r')
    if not core.strip() or core.lstrip().startswith(b'#'):
        continue
    f = core.split(b';')
    if len(f) < 6:
        bad += 1
        continue
    try:
        recs.append((int(f[0]), f[1].decode('ascii'), float(f[2]), float(f[3]), float(f[4])))
    except (ValueError, UnicodeDecodeError):
        bad += 1

P('')
P(f'=== D. buildings.txt 现状 ===  有效记录 {len(recs):,}  异常行 {bad}')

WATER_TYPES = {'floating_harbor'}
res_land, res_water, res_over = [], [], []
by_type = collections.defaultdict(lambda: [0, 0])   # type -> [total, |r|>0.5]
big = []
for (pid, t, x, y, z) in recs:
    h = sample(x, z)
    if h is None:
        continue
    r = y - (A * h + B)
    under = h < LAND_MIN
    if t in WATER_TYPES or under:
        res_water.append(r)
        continue
    res_land.append(r)
    by_type[t][0] += 1
    if abs(r) > 0.5:
        by_type[t][1] += 1
        big.append((abs(r), pid, t, x, z, y, h))
    if h > 250:
        res_over.append((pid, t, x, z, y, h))

rl = np.array(res_land)
rw = np.array(res_water)
P(f'   陆地建筑 {len(rl):,} 条   mean|r|={np.abs(rl).mean():.4f}  max|r|={np.abs(rl).max():.3f}  '
  f'|r|>0.5 的 {int((np.abs(rl)>0.5).sum()):,}')
P(f'   水面建筑 {len(rw):,} 条   mean|r|={np.abs(rw).mean():.4f}  max|r|={np.abs(rw).max():.3f}')
if len(rl):
    for th in (0.5, 1.0, 2.0, 5.0):
        P(f'      |r|>{th}: {int((np.abs(rl)>th).sum()):,}')

P('')
P('=== E. 逐类型「悬空」占比（陆地）===')
for t, (tot, bd) in sorted(by_type.items(), key=lambda kv: -kv[1][1])[:20]:
    P(f'   {t:<32} {bd:>5}/{tot:<7} {100.0*bd/tot if tot else 0:6.2f}%')

P('')
P('=== F. |r| 最大的 30 条 ===')
for (ar, pid, t, x, z, y, h) in sorted(big, key=lambda q: -q[0])[:30]:
    P(f'   省{pid:<6} {t:<30} x={x:8.2f} z={z:8.2f} y={y:8.3f} h={h:6.1f} '
      f'应为={A*h+B:7.3f} r={y-(A*h+B):+8.3f}')

P('')
P(f'=== G. 建在超高地形(h>250)上的建筑 {len(res_over):,} 条 ===')
gg = collections.Counter()
for (pid, t, x, z, y, h) in res_over:
    gg[(int(x//128)*128+64, H-1-(int((H-1-z)//128)*128+64))] += 1
for (gx, gz), c in gg.most_common(12):
    P(f'   图元 x≈{gx:<6} z≈{gz:<6}  {c} 条')
if res_over:
    for (pid, t, x, z, y, h) in sorted(res_over, key=lambda q: -q[5])[:10]:
        P(f'      省{pid:<6} {t:<28} x={x:8.2f} z={z:8.2f} h={h:6.1f} y={y:7.3f}')

# 地形索引合法性
if TW == W and TH == H:
    ta = np.frombuffer(traw[toff:toff + W * H], dtype=np.uint8).reshape(H, W)[::-1]
    idx_used = sorted(set(np.unique(ta).tolist()))
    P('')
    P(f'=== H. terrain 用到的索引 {idx_used} ===')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('WROTE', REP)

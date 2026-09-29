# -*- coding: utf-8 -*-
"""最终判定：
 1) buildings.txt 坐标是否落在大陆（陆地）上；
 2) 用 positions.txt 的省坐标作参照系，计算建筑到「本省坐标」的像素距离；
 3) 用 heightmap 判断建筑点的地形高度（是否落海）；
 4) 判定 victory_points 省份图标位置。
"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_final_judge.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

raw = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
rb = W * 3
a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:rb * H].reshape(H, W, 3)
prov = (a[:, :, 2].astype(np.int32) << 16) | (a[:, :, 1].astype(np.int32) << 8) | a[:, :, 0].astype(np.int32)
rgb2pid = {}
pid_type = {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) >= 5:
            try:
                rgb2pid[(int(f2[1]) << 16) | (int(f2[2]) << 8) | int(f2[3])] = int(f2[0])
                pid_type[int(f2[0])] = f2[4]
            except ValueError:
                pass

hmraw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
ho = struct.unpack_from('<I', hmraw, 10)[0]
hm = np.frombuffer(hmraw, dtype=np.uint8, offset=ho)[:W * H].reshape(H, W)

traw = open(os.path.join(MAP, 'terrain.bmp'), 'rb').read()
to = struct.unpack_from('<I', traw, 10)[0]
ter = np.frombuffer(traw, dtype=np.uint8, offset=to)[:W * H].reshape(H, W)

LAND = hm >= 96
P(f'陆地像素(hm>=96) {int(LAND.sum()):,} / {W*H:,} = {100.0*LAND.mean():.2f}%')

SEA_TYPES = {'ocean', 'sea', 'lake'}
# 从 definition 的 land/ocean 判定
land_pids = {p for p, t in pid_type.items() if t not in SEA_TYPES and t != 'unassigned'}
P(f'definition 里非海/非unassigned 省 {len(land_pids):,}')

P('')
P('=== 1. buildings.txt 坐标 落在陆地/海洋? ===')
cnt = collections.Counter()
by_type = collections.Counter()
offshore = []
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    f = ln.strip().split(';')
    if len(f) < 6:
        continue
    try:
        pid = int(f[0]); t = f[1]; x = float(f[2]); z = float(f[4])
    except ValueError:
        continue
    c = int(x); r = int(z)
    if not (0 <= c < W and 0 <= r < H):
        cnt['越界'] += 1
        continue
    got = rgb2pid.get(int(prov[r, c]))
    h = int(hm[r, c])
    cnt['总计'] += 1
    cnt['落陆地像素'] += int(LAND[r, c])
    cnt['落海像素'] += int(not LAND[r, c])
    cnt['省号一致'] += int(got == pid)
    cnt['落 unassigned/未知'] += int(got is None or pid_type.get(got) == 'unassigned')
    if not LAND[r, c] or (got is not None and pid_type.get(got) in SEA_TYPES):
        by_type[t] += 1
        if len(offshore) < 40:
            offshore.append((pid, got, t, x, z, h, pid_type.get(got, '?')))
for k, v in cnt.items():
    P(f'   {k:<22} {v:,}')

P('')
P('=== 1b. 落在「海像素」上的建筑，按类型 ===')
for t, c in by_type.most_common():
    P(f'   {t:<32} {c:,}')
P('   前 40 条明细:')
for (pid, got, t, x, z, h, ty) in offshore[:40]:
    P(f'      声明省{pid:<6} 落点省{got}({ty:<6}) {t:<28} x={x:8.1f} z={z:8.1f} h={h}')

P('')
P('=== 2. 胜利点省：坐标处的陆地/海 ===')
vp = {}
for dp, _, fs in os.walk(os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')):
    for fn in fs:
        if fn.endswith('.txt'):
            for ln in open(os.path.join(dp, fn), encoding='utf-8', errors='replace'):
                s = ln.split('#')[0].strip()
                if 'victory_points' in s and '=' in s:
                    n = re.findall(r'-?\d+', s.split('=', 1)[1])
                    if len(n) >= 2:
                        vp[int(n[0])] = int(n[1])

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

c2 = collections.Counter()
invp = {}
for pid in vp:
    if pid not in pos:
        c2['无坐标'] += 1
        continue
    x, z = pos[pid]
    cc = int(x); rr = int(z)
    h = int(hm[rr, cc]); onland = LAND[rr, cc]
    c2['总'] += 1
    c2['坐标在陆地'] += int(onland)
    c2['坐标在海'] += int(not onland)
    got = rgb2pid.get(int(prov[rr, cc]))
    c2['坐标落本省'] += int(got == pid)
    c2['坐标落他省'] += int(got != pid)
for k, v in c2.items():
    P(f'   {k:<16} {v}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

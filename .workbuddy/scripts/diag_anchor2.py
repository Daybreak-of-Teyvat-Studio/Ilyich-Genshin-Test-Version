# -*- coding: utf-8 -*-
"""锚点核查 v2（修正映射：row = z, col = x，不翻转）。"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
MAP = os.path.join(MOD, 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_anchor_check2.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

def load_bmp_idx(path):
    raw = open(path, 'rb').read()
    o = struct.unpack_from('<I', raw, 10)[0]
    W, H = struct.unpack_from('<ii', raw, 18)
    bpp = struct.unpack_from('<H', raw, 28)[0]
    if bpp == 24:
        rb = W * 3
        pad = (4 - rb % 4) % 4
        a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:(rb + pad) * H].reshape(H, rb + pad)[:, :rb].reshape(H, W, 3)
        v = a[:, :, 2].astype(np.int32) << 16 | a[:, :, 1].astype(np.int32) << 8 | a[:, :, 0].astype(np.int32)
    else:
        rb = W
        pad = (4 - rb % 4) % 4
        v = np.frombuffer(raw, dtype=np.uint8, offset=o)[:(rb + pad) * H].reshape(H, rb + pad)[:, :rb].astype(np.int32)
    return v, W, H, bpp

prov, W, H, bpp = load_bmp_idx(os.path.join(MAP, 'provinces.bmp'))
P(f'provinces.bmp {W}x{H} {bpp}bpp  -> 用映射 row=z, col=x')

rgb2pid, pid_type = {}, {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) < 5:
            continue
        try:
            rgb2pid[(int(f2[1]) << 16) | (int(f2[2]) << 8) | int(f2[3])] = int(f2[0])
            pid_type[int(f2[0])] = f2[4]
        except ValueError:
            pass

# 高度图
hmraw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
ho = struct.unpack_from('<I', hmraw, 10)[0]
HW, HH = struct.unpack_from('<ii', hmraw, 18)
hm = np.frombuffer(hmraw, dtype=np.uint8, offset=ho)[:HW * HH].reshape(HH, HW)
P(f'heightmap.bmp {HW}x{HH}')

def hval(x, z):
    c = int(x); r = int(z)
    if 0 <= c < HW and 0 <= r < HH:
        return int(hm[r, c])
    return None

def pid_at(x, z):
    c = int(x); r = int(z)
    if 0 <= c < W and 0 <= r < H:
        return rgb2pid.get(int(prov[r, c]))
    return None

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
            pos[cur] = (float(mm.group(1)), float(mm.group(2)), float(mm.group(3))); seen = True

vp_prov = {}
for dirpath, _, files in os.walk(os.path.join(MOD, 'history', 'states')):
    for fn in files:
        if fn.endswith('.txt'):
            for ln in open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace'):
                s = ln.split('#')[0].strip()
                if 'victory_points' in s and '=' in s:
                    nums = re.findall(r'-?\d+', s.split('=', 1)[1])
                    if len(nums) >= 2:
                        vp_prov[int(nums[0])] = int(nums[1])

SEA = {'ocean', 'sea', 'lake'}
UNASSIGNED = {'unassigned'}

P('')
P('=== 1. 全图 positions 坐标 -> 本人省份像素 ===')
tot = hit = 0; badpids = []
for pid, (x, y, z) in pos.items():
    tot += 1
    if pid_at(x, z) == pid:
        hit += 1
    else:
        badpids.append((pid, pid_at(x, z)))
P(f'   {hit:,}/{tot:,} = {100.0*hit/tot:.2f}%')
P(f'   错位 {len(badpids)} 个: {badpids[:40]}')

P('')
P('=== 2. 胜利点省（861）坐标核查 ===')
ok = 0; badl = []; sea_l = []
for pid in sorted(vp_prov):
    if pid not in pos:
        badl.append((pid, '无 positions 记录', None, None)); continue
    x, y, z = pos[pid]
    got = pid_at(x, z)
    h = hval(x, z)
    if got == pid:
        ok += 1
        if pid_type.get(pid, '') in SEA:
            sea_l.append((pid, h, pid_type.get(pid)))
    else:
        badl.append((pid, f'坐标落在省{got}', (round(x, 1), round(z, 1)), pid_type.get(got, '?')))
P(f'   坐标命中本省 {ok}   错位 {len(badl)}')
for (pid, why, xz, ty) in badl[:40]:
    P(f'      省{pid:<6} {why:<22} xz={xz}  落点类型={ty}')
P(f'   胜利点省中「本身是海洋/lake」的 {len(sea_l)} 个:')
for (pid, h, ty) in sea_l[:40]:
    P(f'      省{pid:<6} 类型={ty:<8} 该点高度 h={h}')

P('')
P('=== 3. 建筑坐标 -> 声明的 province_id ===')
bhit = 0; bbadl = []
for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
    s = ln.strip()
    if not s or s.startswith('#'):
        continue
    f = s.split(';')
    if len(f) < 6:
        continue
    try:
        pid = int(f[0]); x = float(f[2]); z = float(f[4])
    except ValueError:
        continue
    got = pid_at(x, z)
    if got == pid:
        bhit += 1
    elif len(bbadl) < 60:
        bbadl.append((pid, got, f[1], x, z, hval(x, z), pid_type.get(got, '?')))
P(f'   命中 {bhit:,}   错位 {len(bbadl)}（最多显示 60）')
for (pid, got, t, x, z, h, ty) in bbadl:
    P(f'      声明省{pid:<6} 实际省{got:<6}({ty:<6}) {t:<28} x={x:8.2f} z={z:8.2f} h={h}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('WROTE', REP)

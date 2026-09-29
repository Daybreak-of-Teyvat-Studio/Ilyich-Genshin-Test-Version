# -*- coding: utf-8 -*-
"""专项：胜利点图标 + 建筑模型 悬空。

胜利点图标位置由引擎按"省份坐标"绘制，省份坐标来自 map/positions.txt。
本脚本：
 1) 解析 positions.txt（块格式）与 definition.csv，核对每个胜利点省的坐标是否落在该省像素内；
 2) 若坐标落在别的省/海里 → 图标必然悬空/错位；
 3) 建筑同理：核对每条建筑 (x,z) 是否落在它声明的 province_id 像素内。
"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
MAP = os.path.join(MOD, 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_anchor_check.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

# ---------- 省份像素图 ----------
raw = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
bpp = struct.unpack_from('<H', raw, 28)[0]
stride = W * (bpp // 8)
pad = (4 - (W * (bpp // 8)) % 4) % 4
rows = []
p = o
for r in range(H):
    row = raw[p:p + W * (bpp // 8)]
    rows.append(row)
    p += W * (bpp // 8) + pad
# 8bpp 下像素是调色板索引，需要调色板
ncol = struct.unpack_from('<I', raw, 46)[0]
pal = []
po = 14 + struct.unpack_from('<I', raw, 14)[0]
for i in range(ncol):
    b, g, rr, _ = raw[po + i * 4: po + i * 4 + 4]
    pal.append((rr, g, b))
prov = np.zeros((H, W), dtype=np.int32)
for r in range(H):
    line = np.frombuffer(rows[r], dtype=np.uint8)
    if bpp == 8:
        arr = np.array([pal[v][0] for v in line], dtype=np.int32) << 16 | \
              np.array([pal[v][1] for v in line], dtype=np.int32) << 8 | \
              np.array([pal[v][2] for v in line], dtype=np.int32)
    else:
        arr = line.reshape(-1, bpp // 8).astype(np.int32)
        arr = arr[:, 0] | (arr[:, 1] << 8) | (arr[:, 2] << 16)
    prov[H - 1 - r] = arr
P(f'provinces.bmp {W}x{H} {bpp}bpp  off={o}')

# ---------- definition.csv: rgb -> pid ----------
rgb2pid = {}
pid_type = {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        f2 = s.split(';')
        if len(f2) < 5:
            continue
        try:
            pid = int(f2[0]); r = int(f2[1]); g = int(f2[2]); b = int(f2[3])
        except ValueError:
            continue
        rgb2pid[(r << 16) | (g << 8) | b] = pid
        pid_type[pid] = f2[4]
P(f'definition.csv 省份 {len(rgb2pid):,} 个')

# ---------- positions.txt ----------
pos = {}
cur = None
seen = False
for ln in open(os.path.join(MAP, 'positions.txt'), 'rb'):
    s = ln.decode('ascii', 'replace').strip()
    m = re.match(r'^(\d+)=\{$', s)
    if m:
        cur = int(m.group(1)); seen = False
        continue
    if cur is not None and not seen:
        mm = re.match(r'^([\d.]+)\s+([\d.]+)\s+([\d.]+)$', s)
        if mm:
            pos[cur] = (float(mm.group(1)), float(mm.group(2)), float(mm.group(3)))
            seen = True
P(f'positions.txt 省份 {len(pos):,} 个')

# ---------- 胜利点省清单 ----------
vp_prov = {}
for dirpath, _, files in os.walk(os.path.join(MOD, 'history', 'states')):
    for fn in files:
        if not fn.endswith('.txt'):
            continue
        for ln in open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace'):
            s = ln.split('#')[0].strip()
            if 'victory_points' in s and '=' in s:
                body = s.split('=', 1)[1]
                nums = re.findall(r'-?\d+', body)
                if len(nums) >= 2:
                    vp_prov[int(nums[0])] = int(nums[1])
P(f'胜利点省份 {len(vp_prov)} 个')

def at(x, z):
    fx = int(x); fy = H - 1 - int(z)
    if 0 <= fx < W and 0 <= fy < H:
        return rgb2pid.get(int(prov[fy, fx]))
    return None

P('')
P('=== 1. 胜利点省：positions.txt 坐标 vs 本人省份像素 ===')
ok = bad = miss = 0
badlist = []
for pid in sorted(vp_prov):
    if pid not in pos:
        miss += 1
        badlist.append((pid, '无 positions 记录', None, None))
        continue
    x, y, z = pos[pid]
    got = at(x, z)
    if got == pid:
        ok += 1
    else:
        bad += 1
        badlist.append((pid, f'坐标落在 {got}', (x, z), pid_type.get(got, '?')))
P(f'   命中 {ok}   错位 {bad}   无记录 {miss}')
for (pid, why, xz, ty) in badlist[:30]:
    P(f'      省{pid:<6} {why:<24} xz={xz}  实际省份类型={ty}')

# ---------- 2. 全图省份坐标 → 省份像素 命中率 ----------
P('')
P('=== 2. 全图 positions 坐标 → 本人省份像素 命中率 ===')
tot = hit = 0
badpids = []
for pid, (x, y, z) in pos.items():
    got = at(x, z)
    tot += 1
    if got == pid:
        hit += 1
    else:
        badpids.append((pid, got))
P(f'   {hit:,}/{tot:,} = {100.0*hit/tot:.2f}%')
if badpids:
    P(f'   错位省份前 30: {[(a,b) for a,b in badpids[:30]]}')

# ---------- 3. 建筑 (x,z) → 省份像素 ----------
P('')
P('=== 3. 建筑坐标 vs 声明的 province_id ===')
bhit = bbad = 0
bbadlist = []
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
    got = at(x, z)
    if got == pid:
        bhit += 1
    else:
        bbad += 1
        if len(bbadlist) < 40:
            bbadlist.append((pid, got, f[1], x, z))
P(f'   命中 {bhit:,}   错位 {bbad:,}   = {100.0*bhit/(bhit+bbad):.2f}%')
for (pid, got, t, x, z) in bbadlist[:25]:
    P(f'      声明省{pid:<6} 实际落在省{got} {t:<26} x={x:8.2f} z={z:8.2f}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('WROTE', REP)

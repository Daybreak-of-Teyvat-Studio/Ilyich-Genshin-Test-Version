# -*- coding: utf-8 -*-
"""dig2.py —— ①40753坏行 ②:679/:716全清单 ③rivers/terrain/heightmap在(4095,480)等4角 ④beta海州行 ⑤INA OOB"""
import os, re, sys, struct

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'

print('=' * 70)
print('【①】gamma buildings.txt 40750-40756 行原文')
ls = open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace').read().split('\n')
for i in range(40748, 40757):
    mark = '>>>' if i == 40752 else '   '
    print(f'  {mark} L{i+1}: {ls[i][:130]!r}')

print()
print('=' * 70)
print('【②】live error.log 中 mapbuildings 全部行号清单')
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
notland = re.findall(r'mapbuildings\.cpp:679\]: map/buildings\.txt error at line (\d+): map building location is not over the land', t)
r716 = re.findall(r'mapbuildings\.cpp:716\]: map/buildings\.txt error at line (\d+)', t)
print(f'  679 "not over land": {len(notland)} 行, 行号: {sorted(set(int(x) for x in notland))}')
print(f'  716 "not within state": {len(r716)} 行, 行号: {sorted(set(int(x) for x in r716))}')
allbad = sorted(set(int(x) for x in notland) | set(int(x) for x in r716))
print(f'  合并 {len(allbad)} 处')
for ln in allbad:
    print(f'    L{ln}: {ls[ln-1][:110]!r}')

print()
print('=' * 70)
print('【③】其他 bmp 在 (4095,480) 族的像素')
def dump_bmp_win(path, name, x0, z0, w=6, h=4):
    raw = open(path, 'rb').read()
    off = struct.unpack('<I', raw[10:14])[0]
    W, H = struct.unpack('<ii', raw[18:26])
    bpp = struct.unpack('<H', raw[28:30])[0]
    RB = W * bpp // 8 if bpp >= 24 else W
    # 8bit indexed: 行 padding 到 4 字节
    rowbytes = ((W * bpp // 8) + 3) // 4 * 4
    print(f'  --- {name} ({W}x{H} bpp={bpp}) @ ({x0},{z0}) ---')
    for z in range(z0, min(z0 + h, H)):
        vals = []
        for x in range(x0, min(x0 + w, W)):
            if bpp == 8:
                vals.append(raw[off + z * rowbytes + x])
            else:
                i = off + z * rowbytes + x * 3
                vals.append((raw[i + 2], raw[i + 1], raw[i]))
        print(f'    z={z:<5}', vals)

for fname in ('rivers.bmp', 'terrain.bmp', 'heightmap.bmp'):
    p = os.path.join(G, 'map', fname)
    if os.path.exists(p):
        for (x0, z0) in ((4090, 478), (4090, 1566), (0, 478), (0, 1566)):
            dump_bmp_win(p, fname, x0, z0)

print()
print('=' * 70)
print('【④】beta buildings.txt 里海州(700-740)的 air_base/fuel_silo 行')
cnt = 0
for l in open(os.path.join(B, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 7 and c[1].strip() in ('air_base', 'fuel_silo', 'radar_station', 'rocket_site_spawn', 'stronghold_network', 'synthetic_refinery', 'nuclear_reactor_spawn') :
        try:
            st = int(c[0])
        except ValueError:
            continue
        if 700 <= st <= 740:
            print('  ', l.strip()[:120])
            cnt += 1
            if cnt > 14:
                break
if cnt == 0:
    print('  （无 —— beta 海州没有这些行？！）')
    # 看看 beta 海州有没有任何行
    for l in open(os.path.join(B, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
        c = l.strip().split(';')
        if len(c) >= 2:
            try:
                st = int(c[0])
            except ValueError:
                continue
            if 700 <= st <= 740:
                print('   any:', l.strip()[:120])
                cnt += 1
                if cnt > 10:
                    break

print()
print('=' * 70)
print('【⑤】INA OOB 里引用 cruiser_2/light_2 的舰船行')
for f in ('INA_1936_Naval.txt', 'INA_1936_naval.txt'):
    p = os.path.join(G, 'history', 'units', f)
    if os.path.exists(p):
        t2 = open(p, encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(r'(?m)^.*(cruiser_2|light_2|heavy_2).*$', t2):
            print('  ', m.group(0).strip()[:130])
            cnt = 0
            cnt += 1
            if cnt > 8:
                break
        # 打印一艘舰的完整块
        mm = re.search(r'ship = \{[^}]*\}', t2)
        if mm:
            print('  样舰块:', mm.group(0)[:300])
        break

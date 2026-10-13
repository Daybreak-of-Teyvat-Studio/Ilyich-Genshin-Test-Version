# -*- coding: utf-8 -*-
"""final_reads.py —— 只读：①(version 0)写法 ②P2/P3交叉全扫 ③beta海州坐标落点"""
import os, re, sys, struct, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')

print('=' * 70)
print('【①】"(version 0)" 在全 units 目录的出现')
for tag, base in (('gamma', G), ('beta', B)):
    hits = []
    for f in glob.glob(os.path.join(base, 'history', 'units', '*')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        n = t.count('(version 0)')
        if n:
            hits.append((os.path.basename(f), n))
    print(f'  [{tag}] {hits}')
print()
print('  gamma INA_1936_Naval.txt 中 (version 0) 的上下文:')
p = os.path.join(G, 'history', 'units', 'INA_1936_Naval.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
for m in list(re.finditer(r'ship = \{[^\n]*\(version 0\)[^\n]*', t))[:6]:
    print('   ', m.group(0).strip()[:250])
print(f'   共 {t.count("(version 0)")} 处')
print()
p = os.path.join(G, 'history', 'units', 'FAV_1936_Naval.txt')
if os.path.exists(p):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for m in list(re.finditer(r'ship = \{[^\n]*\(version 0\)[^\n]*', t))[:4]:
        print('   FAV:', m.group(0).strip()[:250])
    print(f'   FAV 共 {t.count("(version 0)")} 处')

print()
print('=' * 70)
print('【②】provinces.bmp 全扫 P2/P3 三色交叉 + 四色（此前只扫过棋盘/四色）')
raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
W, H = struct.unpack('<ii', raw[18:26])
RB = W * 3
colors = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            colors[(int(c[1]), int(c[2]), int(c[3]))] = int(c[0])
        except ValueError:
            pass

def pid(i):
    return colors.get((raw[i + 2], raw[i + 1], raw[i]))

P2 = []   # a==d, b!=c, 且 b,c 都 != a
P3 = []   # b==c, a!=d, 且 a,d 都 != b
for z in range(H - 1):
    base = off + z * RB
    nb = base + RB
    for x in range(W - 1):
        i = base + x * 3
        j = i + 3
        a = pid(i)
        b = pid(j)
        c = pid(nb + x * 3)
        d = pid(nb + x * 3 + 3)
        if a is None or b is None or c is None or d is None:
            continue
        if a == d and b != c and b != a and c != a:
            P2.append((x, z, a, b, c))
        elif b == c and a != d and a != b and d != b:
            P3.append((x, z, a, b, d))
print(f'  P2 (A B/A C 型): {len(P2)} 处')
for x, z, a, b, c in P2[:15]:
    print(f'    ({x},{z}) A={a} B={b} C={c}')
print(f'  P3 (A B/D B 型): {len(P3)} 处')
for x, z, a, b, d in P3[:15]:
    print(f'    ({x},{z}) A={a} B={b} D={d}')
# 距 (4095,480) / (4095,1567) / (0,480) / (0,1567) 最近的
for name, arr in (('P2', P2), ('P3', P3)):
    for (tx, tz) in ((4095, 480), (4095, 1567), (0, 480), (0, 1567)):
        if arr:
            nx = min(arr, key=lambda t: abs(t[0] - tx) + abs(t[1] - tz))
            d = abs(nx[0] - tx) + abs(nx[1] - tz)
            if d < 60:
                print(f'  {name} 距({tx},{tz}) 最近: ({nx[0]},{nx[1]}) 距={d}')

print()
print('=' * 70)
print('【③】beta 海州 air_base 行坐标在 beta 地图上的落点')
bk = {}
for l in open(os.path.join(B, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            bk[(int(c[1]), int(c[2]), int(c[3]))] = (int(c[0]), c[4])
        except ValueError:
            pass
braw = open(os.path.join(B, 'map', 'provinces.bmp'), 'rb').read()
boff = struct.unpack('<I', braw[10:14])[0]
BW, BH = struct.unpack('<ii', braw[18:26])
BRB = BW * 3
print(f'  beta 地图: {BW}x{BH}')
# beta 海州既有建筑的坐标（例：700 air_base 2373,1817；702 air_base 2446,1862）
for (x, z) in ((2373, 1817), (2446, 1862), (2322, 1871)):
    for flipname, zz in (('直读', z), ('翻转', BH - 1 - z)):
        i = boff + zz * BRB + x * 3
        p = bk.get((braw[i + 2], braw[i + 1], braw[i]))
        print(f'    ({x},{z}) {flipname} → 省{p}')
print()
print('  参照：beta 普通陆地州的行（如 beta s1 的某 air_base）落点')
cnt = 0
for l in open(os.path.join(B, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 7 and c[1].strip() == 'air_base':
        try:
            st = int(c[0])
            x = int(float(c[2]))
            z = int(float(c[4]))
        except ValueError:
            continue
        if st in (1, 2, 3):
            i = boff + z * BRB + x * 3
            p = bk.get((braw[i + 2], braw[i + 1], braw[i]))
            print(f'    beta s{st} air_base ({x},{z}) → 省{p}')
            cnt += 1
            if cnt >= 3:
                break

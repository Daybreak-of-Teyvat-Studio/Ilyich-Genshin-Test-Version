# -*- coding: utf-8 -*-
"""xcross_scan2.py —— 双副本 bmp 对比 + 两种歧义图案全扫"""
import os, sys, time, struct, hashlib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

gk, colors = {}, {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            pid = int(c[0])
        except ValueError:
            continue
        gk[pid] = c[4]
        colors[(int(c[1]), int(c[2]), int(c[3]))] = pid

for tag, base in (('仓库', G), ('副本', D)):
    p = os.path.join(base, 'map', 'provinces.bmp')
    if not os.path.exists(p):
        print(f'{tag}: 不存在')
        continue
    raw = open(p, 'rb').read()
    mt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))
    md5 = hashlib.md5(raw).hexdigest()
    off = struct.unpack('<I', raw[10:14])[0]
    W, H = struct.unpack('<ii', raw[18:26])
    RB = W * 3
    t0 = time.time()
    checker, quad = [], []
    for z in range(H - 1):
        base_i = off + z * RB
        nbase = base_i + RB
        for x in range(W - 1):
            i = base_i + x * 3
            j = i + 3
            a = colors.get((raw[i + 2], raw[i + 1], raw[i]))
            b = colors.get((raw[j + 2], raw[j + 1], raw[j]))
            c = colors.get((raw[nbase + x * 3 + 2], raw[nbase + x * 3 + 1], raw[nbase + x * 3]))
            d = colors.get((raw[nbase + x * 3 + 5], raw[nbase + x * 3 + 4], raw[nbase + x * 3 + 3]))
            if a is None or b is None or c is None or d is None:
                continue
            if a == d and b == c and a != b:
                checker.append((x, z, a, b))
            elif len({a, b, c, d}) == 4:
                quad.append((x, z, a, b, c, d))
    print(f'{tag}: {len(raw):,}B md5={md5[:12]} mtime={mt} 尺寸={W}x{H}')
    print(f'  棋盘交叉(A B/B A): {len(checker)} 处')
    for x, z, a, b in checker[:10]:
        print(f'    ({x},{z}) {a}({gk.get(a)})/{b}({gk.get(b)}) 距东缘(4095,480维)=?')
    print(f'  四省交叉(A B/C D): {len(quad)} 处')
    for x, z, a, b, c, d in quad[:10]:
        print(f'    ({x},{z}) {a}/{b}/{c}/{d}')
    # 距 (4095,480) 最近的
    if checker:
        nx = min(checker, key=lambda t: abs(t[0] - 4095) + abs(t[1] - 480))
        print(f'  棋盘交叉最近(4095,480直读): ({nx[0]},{nx[1]}) 距={abs(nx[0]-4095)+abs(nx[1]-480)}')
        ny = min(checker, key=lambda t: abs(t[0] - 4095) + abs(t[1] - 1568))
        print(f'  棋盘交叉最近(4095,1568镜像): ({ny[0]},{ny[1]}) 距={abs(ny[0]-4095)+abs(ny[1]-1568)}')
    if quad:
        nq = min(quad, key=lambda t: abs(t[0] - 4095) + abs(t[1] - 480))
        print(f'  四省交叉最近(4095,480): ({nq[0]},{nq[1]}) 距={abs(nq[0]-4095)+abs(nq[1]-480)}')
    print(f'  扫描 {time.time()-t0:.1f}s')
    print()

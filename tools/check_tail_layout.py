# -*- coding: utf-8 -*-
"""check_tail_layout.py —— 尾部布局核实：708/709(海) vs 718/750(陆) + 引用扫描"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

kind = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        kind[int(a[0])] = a[4]

print('=== 尾段布局（700-750）===')
layout = []
for sid in range(700, 751):
    f = os.path.join(ST, f'{sid}-State_{sid}.txt')
    if not os.path.exists(f):
        layout.append((sid, '缺文件', None, 0))
        continue
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in (pm.group(1).split() if pm else [])]
    land_n = sum(1 for p in provs if kind.get(p) == 'land')
    nm = re.search(r'name\s*=\s*"([^"]*)"', t)
    layout.append((sid, '陆' if land_n else '海', om.group(1) if om else None, len(provs)))
    print(f'  s{sid}: {"陆" if land_n else "海"} owner={om.group(1) if om else "无"} 省{len(provs)} {nm.group(1) if nm else ""}')

print()
print('=== 四州文件内容 ===')
for sid in (708, 709, 718, 750):
    f = os.path.join(ST, f'{sid}-State_{sid}.txt')
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    print(f'--- s{sid} ---')
    print('  ' + t.replace(chr(10), ' | ')[:260])
    print()

print('=== 引用扫描（708/709/718/750 作为州号）===')
targets = {708, 709, 718, 750}
# capitals
for p in glob.glob(os.path.join(G, 'history', 'countries', '*.txt')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'(?m)^\s*capital\s*=\s*(\d+)', t):
        if int(m.group(1)) in targets:
            print(f'  首都: {os.path.basename(p)} capital = {m.group(1)}')
# localisation
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'(?m)^\s*DOT_STATE_(708|709|718|750):\d*\s*"([^"]*)"', t):
        print(f'  loc: {os.path.basename(p)} DOT_STATE_{m.group(1)} = "{m.group(2)}"')
# buildings first col
raw = open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read().decode('utf-8-sig')
cnt = collections.Counter()
for l in raw.split('\r\n'):
    f7 = l.split(';')
    if len(f7) == 7 and f7[0].isdigit() and int(f7[0]) in targets:
        cnt[int(f7[0])] += 1
print('  buildings 行数:', dict(cnt))
# 脚本引用
n = 0
for root, dirs, files in os.walk(G):
    dirs[:] = [d for d in dirs if d not in ('.backups', '.backup', '.git', '备份', 'map', 'localisation')]
    for f in files:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(root, f)
        rr = os.path.relpath(p, G).replace('\\', '/')
        if rr.startswith('history/states'):
            continue
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        for i, l in enumerate(t.splitlines(), 1):
            for m in re.finditer(r'\b(state|capital|owns_state|controls_state|transfer_state)\s*=\s*(708|709|718|750)\b', l):
                n += 1
                if n <= 25:
                    print(f'  脚本: {rr}:{i} {l.strip()[:100]}')
print(f'  脚本引用共 {n} 处')

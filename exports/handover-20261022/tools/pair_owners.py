# -*- coding: utf-8 -*-
"""pair_owners.py —— 六对两端 + 未命名稻妻州的完整画像"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read().split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = c[4]
        except ValueError:
            pass
allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()

def loc_of(sid):
    m = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    return m.group(1) if m else '★无'

def info(sid):
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{sid}*.txt'))
          if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    if not fs:
        return '★无文件'
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    ps = [int(x) for x in re.findall(r'\d+', m.group(1))] if m else []
    kinds = set(gk.get(p) for p in ps)
    ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
    return f'{len(ps)}省 kind={kinds} owner={ow.group(1) if ow else "-"} 省例={ps[:5]}'

print('=== 六对两端 ===')
for a, b in ((136, 741), (254, 748), (574, 744), (636, 745), (695, 747), (None, 740)):
    if a:
        print(f'  {a}: loc={loc_of(a):14s} {info(a)}')
    print(f'  {b}: loc={loc_of(b):14s} {info(b)}')
    print()

print('=== 未命名稻妻州（③里的 * 州）===')
for sid in (103, 108, 113, 115, 126):
    print(f'  {sid}: loc={loc_of(sid):10s} {info(sid)}')

print()
print('=== gamma_l 文件里 120-140 / 250-260 行附近（看坐标邻接的命名块）===')
p = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
ls = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
for rng in ((125, 150), (240, 262), (565, 580), (628, 645), (688, 700)):
    print(f'  --- L{rng[0]}-{rng[1]} ---')
    for j in range(rng[0] - 1, min(len(ls), rng[1])):
        print(f'   L{j+1}: {ls[j].strip()[:90]}')

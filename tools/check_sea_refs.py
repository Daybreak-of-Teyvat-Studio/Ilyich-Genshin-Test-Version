# -*- coding: utf-8 -*-
"""check_sea_refs.py —— 海州清单 + 首都/引用指向海州的检查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

kind = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        kind[int(a[0])] = a[4]

sea_states, land_states = [], []
for f in sorted(glob.glob(os.path.join(ST, '*.txt'))):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in (pm.group(1).split() if pm else [])]
    land_n = sum(1 for p in provs if kind.get(p) == 'land')
    (sea_states if land_n == 0 else land_states).append(sid)

print(f'海州（无陆地省）{len(sea_states)} 个:')
print(' ', sea_states)

print()
print('=== 首都指向海州的国家 ===')
bad_caps = []
for p in glob.glob(os.path.join(G, 'history', 'countries', '*.txt')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'(?m)^\s*capital\s*=\s*(\d+)', t):
        c = int(m.group(1))
        if c in sea_states:
            bad_caps.append((os.path.basename(p), c))
print(bad_caps if bad_caps else '  无 ✓')

print()
print('=== 全国文件里其他指向海州的引用（state = N / 数字键） ===')
sea_set = set(sea_states)
hits = []
for p in glob.glob(os.path.join(G, 'history', 'countries', '*.txt')) + \
         glob.glob(os.path.join(G, 'history', 'units', '*.txt')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'\b(\w+)\s*=\s*(\d+)\b', t):
        if int(m.group(2)) in sea_set and m.group(1) in ('state', 'capital', 'location', 'province'):
            hits.append((os.path.relpath(p, G), m.group(0)))
for h in hits[:20]:
    print(' ', h)
print(f'  共 {len(hits)} 处')

# 重复省份归属检查
seen = {}
dup = []
for f in sorted(glob.glob(os.path.join(ST, '*.txt'))):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        q = int(x)
        if q in seen:
            dup.append((q, seen[q], sid))
        seen[q] = sid
print()
print(f'重复归属省: {len(dup)} {dup[:10]}')

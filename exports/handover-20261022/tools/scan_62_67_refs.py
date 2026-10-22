# -*- coding: utf-8 -*-
"""scan_62_67_refs.py —— 州 62/63/64/65/66/67 的全引用扫描（只读）"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

IDS = ('62', '63', '64', '65', '66', '67')
PAT = re.compile(r'((?:state|owns_state|controls_state|transfer_state|capital|state_id)\s*=\s*)(' + '|'.join(IDS) + r')(?!\d)')
BARE = re.compile(r'(?m)^(\s*)(' + '|'.join(IDS) + r')(\s*=\s*\{)')

print('=== ① state 语法引用 ===')
n = 0
for sub in ('common', 'events', 'history'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        if 'states' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if 'resource_prospecting' in rel or '14_sea' in rel or '12_wuw' in rel:
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for i, l in enumerate(t.split('\n')):
                for m in PAT.finditer(l):
                    print(f'  {rel} L{i+1}: {l.strip()[:130]}')
                    n += 1
print(f'  共 {n} 处')

print()
print('=== ② 裸作用域 ===')
n = 0
for sub in ('common', 'events'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if 'resource_prospecting' in rel or '14_sea' in rel or '12_wuw' in rel:
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for i, l in enumerate(t.split('\n')):
                m = BARE.match(l)
                if m:
                    print(f'  {rel} L{i+1}: {l.strip()[:130]}')
                    n += 1
print(f'  共 {n} 处')

print()
print('=== ③ loc 键（62-67）===')
allloc = ''
import glob
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()
for sid in (62, 63, 64, 65, 66, 67):
    m = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    print(f'  DOT_STATE_{sid} = {m.group(1) if m else "★无键"}')

print()
print('=== ④ 这 8 个省的战略区归属（现在都在区域1吗）===')
PROVS = ['4681', '3544', '4682', '4683', '4684', '860', '1531', '2282']
p = os.path.join(G, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
# 区域文件 = 逐行省号
ls = [x.strip() for x in t.split('\n') if x.strip()]
for pv in PROVS:
    print(f'  省{pv}: {"∈区域1" if pv in ls else "★不在区域1"}')

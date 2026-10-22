# -*- coding: utf-8 -*-
"""audit_lastnight.py —— 昨晚补号操作(89/90/94←707/708/709 + 并入86)的完整性审计"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()

print('=== ① loc 键现状（89/90/94 = 新内容；707/708/709/86 = 旧键应为死键）===')
for sid in (86, 89, 90, 94, 706, 707, 708, 709):
    m = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    print(f'  DOT_STATE_{sid} = {m.group(1) if m else "★无键"}')

print()
print('=== ② airports/rocketsites 键 ===')
for fname in ('airports.txt', 'rocketsites.txt'):
    t = open(os.path.join(G, 'map', fname), encoding='utf-8-sig', errors='replace').read()
    for sid in (86, 89, 90, 94, 706, 707, 708, 709):
        m = re.search(rf'(?m)^\s*{sid}\s*=\s*\{{([^}}]*)\}}', t)
        print(f'  {fname} s{sid}: {m.group(1).strip() if m else "★无键"}')

print()
print('=== ③ buildings 行数（86/89/90/94/706/707/708/709）===')
bp = os.path.join(G, 'map', 'buildings.txt')
cc = {}
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    c = l.split(';')
    if c and c[0].strip() in ('86', '89', '90', '94', '706', '707', '708', '709'):
        cc[c[0].strip()] = cc.get(c[0].strip(), 0) + 1
print(f'  {cc}')

print()
print('=== ④ 脚本/国策等对旧号 89/90/94/707/708/709 的引用 ===')
PAT = re.compile(r'((?:state|owns_state|controls_state|transfer_state|capital|state_id)\s*=\s*)(89|90|94|706|707|708|709)(?!\d)')
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

print()
print('=== ⑤ 裸作用域 89/90/94/707-709 ===')
BARE = re.compile(r'(?m)^\s*(89|90|94|706|707|708|709)\s*=\s*\{')
for sub in ('common', 'events'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if 'resource_prospecting' in rel:
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for i, l in enumerate(t.split('\n')):
                if BARE.match(l):
                    print(f'  {rel} L{i+1}: {l.strip()[:120]}')

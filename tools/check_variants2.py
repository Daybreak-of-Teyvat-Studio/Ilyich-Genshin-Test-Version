# -*- coding: utf-8 -*-
"""check_variants2.py —— PRI 变体块详查 + INA/FAV OOB 的 version_name 需求"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== PRI 国家文件的 4 个变体块 ===')
p = os.path.join(G, 'history', 'countries', 'PRI - Principles.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
for m in re.finditer(r'create_equipment_variant\s*=\s*\{', t):
    depth, i = 0, m.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    print(t[m.start():i + 1][:700])
    print('---')

print()
print('=== INA / FAV OOB 里的版本名需求（hull → version_name）===')
for tag in ('INA', 'FAV'):
    used = {}
    for f in glob.glob(os.path.join(G, 'history', 'units', f'{tag}_*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(r'(ship_hull_\w+) = \{ amount = \d+ owner = ' + tag + r' version_name = "([^"]+)"', t):
            used.setdefault(m.group(1), set()).add(m.group(2))
    print(f'  {tag}: {used}')

# -*- coding: utf-8 -*-
"""last_count.py —— 全 units 目录数 INA/FAV 的 hull 引用次数"""
import os, sys, glob, re, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('======== history/units 目录下的 INA* / FAV* 文件 ========')
for f in sorted(glob.glob(os.path.join(G, 'history', 'units', '*'))):
    b = os.path.basename(f)
    if b.startswith(('INA', 'FAV')):
        print(f'  {b}: {os.path.getsize(f)}B')

print()
print('======== 全 units 目录里各 hull 的引用计数（country=INA/FAV） ========')
cnt = collections.Counter()
for f in sorted(glob.glob(os.path.join(G, 'history', 'units', '*'))):
    b = os.path.basename(f)
    tag = None
    if b.startswith('INA'):
        tag = 'INA'
    elif b.startswith('FAV'):
        tag = 'FAV'
    if not tag:
        continue
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    for hull in ('ship_hull_cruiser_1', 'ship_hull_cruiser_2', 'ship_hull_light_1',
                 'ship_hull_light_2', 'ship_hull_heavy_2'):
        n = len(re.findall(re.escape(hull) + r'\s*=', t))
        if n:
            cnt[(b, hull)] = n
for (b, hull), n in sorted(cnt.items()):
    print(f'  {b}: {hull} ×{n}')

print()
print('======== INA_1936_Naval.txt 里 cruiser_2/light_2 全部的船（逐行） ========')
p = os.path.join(G, 'history', 'units', 'INA_1936_Naval.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
for m in re.finditer(r'ship = \{[^\n]*', t):
    l = m.group(0)
    if 'cruiser_2' in l or 'light_2' in l:
        print('  ', l.strip()[:200])
print()
print('======== FAV 两个新增变体块全文 ========')
p = os.path.join(G, 'history', 'countries', 'FAV - Favonius.txt')
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
    blk = t[m.start():i + 1]
    if 'Mondstadt_Class' in blk or 'Fontaine_Class' in blk:
        print('  ---')
        for l in blk.split('\n'):
            print('   ', l.rstrip()[:120])

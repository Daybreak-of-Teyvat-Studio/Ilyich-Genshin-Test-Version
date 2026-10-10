# -*- coding: utf-8 -*-
"""check_plane_variant.py —— 闲云机-26型 失败诊断"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== DOT_on_actions.txt 1-60 行（on_action 名与循环结构）===')
p = os.path.join(G, 'common', 'on_actions', 'DOT_on_actions.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read().splitlines()
for i, l in enumerate(t[:60], 1):
    print(f'{i}: {l[:130]}')

print()
print('=== bomb_locks 定义搜索（mod + 原版）===')
for base, tag in ((G, 'mod'), (r'F:\Steam\steamapps\common\Hearts of Iron IV', '原版')):
    hits = []
    for p in glob.glob(os.path.join(base, 'common', 'units', 'equipment', 'modules', '*.txt')) + \
             glob.glob(os.path.join(base, 'common', 'units', 'equipment', '*.txt')):
        tt = open(p, encoding='utf-8-sig', errors='replace').read()
        if 'bomb_locks' in tt:
            for m in re.finditer(r'(?m)^.{0,20}bomb_locks.{0,120}$', tt):
                hits.append((os.path.relpath(p, base), m.group(0).strip()[:140]))
    print(f'  [{tag}] {len(hits)} 处:')
    for h in hits[:12]:
        print('   ', h)

print()
print('=== mod 的 plane modules 文件与槽位 ===')
for p in glob.glob(os.path.join(G, 'common', 'units', 'equipment', 'modules', '*plane*')) + \
         glob.glob(os.path.join(G, 'common', 'units', 'equipment', 'modules', '*air*')):
    print('  ', os.path.relpath(p, G))

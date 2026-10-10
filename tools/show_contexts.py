# -*- coding: utf-8 -*-
"""show_contexts.py —— diff 剩余 + 三处修改点当前语境"""
import os, sys, difflib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BK = os.path.join(ROOT, '.backups', 'tower1314_20261008_130216')

old = open(os.path.join(BK, 'DVA_focustree.txt'), encoding='utf-8-sig', errors='replace').read().splitlines()
new = open(os.path.join(D, 'common', 'national_focus', 'DVA_focustree.txt'), encoding='utf-8-sig', errors='replace').read().splitlines()
diff = list(difflib.unified_diff(old, new, lineterm='', n=0))
print('=== focustree 完整 diff ===')
for x in diff:
    print(x[:150])

print()
for rng in ((1840, 1860), (1915, 1930), (255, 285), (1820, 1832)):
    print(f'--- focustree {rng[0]}-{rng[1]} ---')
    for i in range(rng[0] - 1, min(rng[1], len(new))):
        print(f'{i+1}: {new[i].rstrip()[:110]}')
    print()

anr = open(os.path.join(D, 'common', 'on_actions', 'ANR_influence_on_actions.txt'), encoding='utf-8-sig', errors='replace').read().splitlines()
print('--- ANR 374-392 ---')
for i in range(373, min(392, len(anr))):
    print(f'{i+1}: {anr[i].rstrip()[:110]}')

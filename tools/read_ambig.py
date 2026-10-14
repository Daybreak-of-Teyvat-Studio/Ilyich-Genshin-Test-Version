# -*- coding: utf-8 -*-
"""read_ambig.py —— 读清楚 ①94.id 语法 ②FON/DRA 的 90 上下文 ③common/names 归属"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'

def show(rel, ln, span=6):
    p = os.path.join(G, *rel.split('\\'))
    ls = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
    print(f'--- {rel} L{ln}±{span} ---')
    for i in range(max(0, ln - span - 1), min(len(ls), ln + span)):
        print(f'  L{i+1}: {ls[i].rstrip()[:120]}')
    print()

show('common\\scripted_localisation\\DOT_wonder_state_scripted_localisation.txt', 28, 8)
show('common\\national_focus\\FON_focus.txt', 614, 8)
show('common\\scripted_effects\\DRA_scripted_effects.txt', 698, 8)
show('common\\scripted_effects\\LYY_scripted_effects.txt', 118, 8)

print('=== common/names/00_names.txt 是原版的吗 ===')
p1 = os.path.join(G, 'common', 'names', '00_names.txt')
p2 = os.path.join(V, 'common', 'names', '00_names.txt')
print(f'  原版有: {os.path.exists(p2)}')
if os.path.exists(p2):
    import hashlib
    h1 = hashlib.md5(open(p1, 'rb').read()).hexdigest()
    h2 = hashlib.md5(open(p2, 'rb').read()).hexdigest()
    print(f'  与 mod 版 md5 相同: {h1 == h2}')

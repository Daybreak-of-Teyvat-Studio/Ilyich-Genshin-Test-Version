# -*- coding: utf-8 -*-
"""sum372.py —— SUM 文件里 372 的全部出处 + 浪船景点决策定位"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== SUM 三文件中的 372 ===')
for rel in (os.path.join('common', 'decisions', 'SUM_decisions.txt'),
            os.path.join('common', 'scripted_effects', 'SUM_scripted_effects.txt'),
            os.path.join('common', 'dynamic_modifiers', 'SUM_dynamic_modifiers.txt')):
    p = os.path.join(G, rel)
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'--- {os.path.basename(rel)} ---')
    for i, l in enumerate(t.split('\n')):
        if re.search(r'(?<!\d)372(?!\d)', l):
            print(f'  L{i+1}: {l.strip()[:125]}')
    print()

print('=== 全 common 搜 Ormos_Waverider（含第二决策）===')
for f in glob.glob(os.path.join(G, 'common', '**', '*.txt'), recursive=True):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    if 'Ormos_Waverider' in t:
        rel = os.path.relpath(f, G)
        for i, l in enumerate(t.split('\n')):
            if 'Ormos_Waverider' in l:
                print(f'  {rel} L{i+1}: {l.strip()[:125]}')

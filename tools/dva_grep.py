# -*- coding: utf-8 -*-
"""dva_grep.py —— DVA 文件里待修模式的全部出现处与语境"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
G = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'Daybreak of Teyvat Gamma Version')

for path, pats in (
    ('common/national_focus/DVA_focustree.txt', [r'(?m)^\s*60\s*=\s*\{', r'(?m)^\s*76\s*=\s*\{',
                                                   r'province\s*=\s*1314', r'\bid\s*=\s*1314', r'= 1314\b']),
    ('common/on_actions/ANR_influence_on_actions.txt', [r'state\s*=\s*60\b', r'controls_province', r'= 1314\b']),
    ('common/decisions/DVA_decisions.txt', [r'= 1314\b', r'province\s*=', r'\bid\s*=\s*\d+']),
):
    t = open(os.path.join(G, path), encoding='utf-8-sig', errors='replace').read().splitlines()
    print(f'=== {path} ===')
    for pat in pats:
        hits = [(i, l.strip()) for i, l in enumerate(t, 1) if re.search(pat, l)]
        print(f'  [{pat}] {len(hits)} 处')
        for i, l in hits[:12]:
            print(f'    {i}: {l[:100]}')
    print()

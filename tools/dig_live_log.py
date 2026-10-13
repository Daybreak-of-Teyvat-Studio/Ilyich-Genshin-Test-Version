# -*- coding: utf-8 -*-
"""dig_live_log.py —— 全日志搜 strategicair / mapbuildings / site / port / naval 等关键行"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
lines = t.split('\n')

PATTERNS = [
    ('strategicair', r'strategicair'),
    ('mapbuildings', r'mapbuildings'),
    ('有 site 字样', r'(?i)\bsite\b'),
    ('port/naval', r'(?i)\bnaval\b|\bport\b|harbor'),
    ('map.cpp', r'map\.cpp'),
    ('provincetemplate/state', r'(?i)provincetemplate|state #'),
    ('317 相关', r'\b317\b'),
]
for name, pat in PATTERNS:
    rx = re.compile(pat)
    hits = [l.strip() for l in lines if rx.search(l)]
    print(f'===== {name}: {len(hits)} 行 =====')
    seen = collections.OrderedDict()
    for l in hits:
        k = re.sub(r'\d+', '#', l)[:150]
        if k not in seen:
            seen[k] = l[:240]
    for k, sample in list(seen.items())[:25]:
        print('  ', sample)
    print()

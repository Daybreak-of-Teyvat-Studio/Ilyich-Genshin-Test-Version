# -*- coding: utf-8 -*-
"""find_check_strings.py —— 搜 IsMapInGoodState 检查的全部报错文案"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
LOG = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
t = open(LOG, encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]

PATS = ['has no state', 'has no provinces', 'separated from the rest', 'Strategic region',
        'Definition for state id', 'MAP_ERROR: State', 'land province', 'is coastal. Bitmap',
        'no pixels in provinces.bmp', 'TOO LARGE BOX', 'added twice', 'no straits']
for p in PATS:
    hits = [l.strip() for l in lines if p.lower() in l.lower()]
    print(f'=== "{p}": {len(hits)} 条 ===')
    for h in hits[:8]:
        print('  ', h[:200])

print()
print('=== 全部含 "MAP_ERROR" 的行 ===')
n = 0
for l in lines:
    if 'MAP_ERROR' in l:
        print('  ', l.strip()[:200])
        n += 1
print(f'恰好 {n} 条')

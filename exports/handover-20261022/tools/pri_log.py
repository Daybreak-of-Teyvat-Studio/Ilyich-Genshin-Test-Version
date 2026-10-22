# -*- coding: utf-8 -*-
"""pri_log.py —— debug 日志中 PRI/ship.cpp 行及上下文"""
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()
idx = [i for i, l in enumerate(ls) if 'PRI' in l or 'ship.cpp' in l or 'variant for type' in l]
print('PRI/ship/variant 行数:', len(idx))
seen = set()
shown = 0
for i in idx:
    key = ls[i].split(']')[-1][:60]
    if key in seen:
        continue
    seen.add(key)
    shown += 1
    print('---')
    for j in range(max(0, i - 2), min(len(ls), i + 3)):
        print(f'{j+1}: {ls[j][:175]}')
    if shown >= 6:
        break

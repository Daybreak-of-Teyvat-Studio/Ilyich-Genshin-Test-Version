# -*- coding: utf-8 -*-
"""read_id_errors.py —— "Failed to create id" 的完整行与上下文"""
import re, sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()

idx = [i for i, l in enumerate(ls) if 'Failed to create id' in l]
print(f'“Failed to create id” 共 {len(idx)} 处')
for i in idx:
    print(f'  行{i+1}: {ls[i][:170]}')

if idx:
    i = idx[0]
    print()
    print('=== 首次出现前 30 行上下文 ===')
    for j in range(max(0, i - 30), min(len(ls), i + 12)):
        mark = '>>>' if j == i else '   '
        print(f'{mark} {j+1}: {ls[j][:175]}')

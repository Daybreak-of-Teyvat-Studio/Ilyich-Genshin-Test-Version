# -*- coding: utf-8 -*-
"""grep_fatal.py —— 在最新 error.log 找致命线索"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()
print('总行数', len(ls))

KEYS = ('fatal', 'FATAL', 'Fatal', 'DVA', 'unit', 'template', 'location', 'invalid', 'Invalid',
        'unknown', 'Unknown', 'missing', 'Missing')
hits = collections.Counter()
sample = {}
for i, l in enumerate(ls, 1):
    for k in KEYS:
        if k in l:
            key = re.sub(r'\d+', '#', l.split(']')[-1][:80])
            hits[key] += 1
            sample.setdefault(key, (i, l[:170]))
            break
print('=== 关键词错误分类 ===')
for k, v in hits.most_common(30):
    i, s = sample[k]
    print(f'{v:5d}  {s}')

# 最后 500 行里非 GUI 的
print()
print('=== 尾部 800 行中非 frontend/gui 的 ===')
n = 0
for l in ls[-800:]:
    if 'containerwindow' in l or 'frontendgamesetupview' in l:
        continue
    n += 1
    if n <= 30:
        print(l[:170])
print('（非 GUI 行数: %d）' % n)

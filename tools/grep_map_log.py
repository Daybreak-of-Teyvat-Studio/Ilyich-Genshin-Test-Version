# -*- coding: utf-8 -*-
"""grep_map_log.py —— 搜日志中地图加载相关的关键行"""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
KEYS = ('provinces.bmp', 'definition.csv', 'default.map', 'gamma', 'Gamma',
        'Failed', 'failed', 'Could not', 'Unable', 'corrupt', 'Corrupt', 'invalid map', 'map/')
hits = []
for i, l in enumerate(open(P, encoding='utf-8', errors='replace'), 1):
    if any(k in l for k in KEYS):
        hits.append((i, l.rstrip()))
print(f'命中 {len(hits)} 行')
for i, l in hits[:60]:
    print(f'{i}: {l[:170]}')

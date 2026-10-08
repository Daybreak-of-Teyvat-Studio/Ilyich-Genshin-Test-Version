# -*- coding: utf-8 -*-
"""grep_all_logs.py —— 全日志搜 Loaded/地图加载标记"""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'
KEYS = ('Loaded', 'provinces', 'provinces.bmp', 'strategic region', 'states loaded',
        'Loading map', 'map loaded', 'Map', 'province definitions')
for f in sorted(os.listdir(D)):
    p = os.path.join(D, f)
    if not os.path.isfile(p) or not f.endswith('.log'):
        continue
    try:
        ls = open(p, encoding='utf-8', errors='replace').read().splitlines()
    except Exception:
        continue
    hits = [(i, l) for i, l in enumerate(ls, 1)
            if any(k in l for k in KEYS) and 'MAP_ERROR' not in l
            and 'loaded \'' not in l and '#0' not in l and 'loaded' not in l.split(']')[-1][:8]]
    # 宽松打印：只看含 Loaded 关键词且不是"xxx loaded" 模板行
    hits2 = [(i, l) for i, l in enumerate(ls, 1)
             if ('Loaded' in l or 'provinces' in l) and 'MAP_ERROR' not in l]
    if hits2:
        print(f'--- {f} ---')
        for i, l in hits2[:30]:
            print(f'  {i}: {l.rstrip()[:170]}')

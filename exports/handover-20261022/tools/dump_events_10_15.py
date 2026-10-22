# -*- coding: utf-8 -*-
"""dump_events_10_15.py —— 完整打印 .10 与 .15 事件定义对比"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'events', 'DOT_CityControl_Event.txt')
t = open(P, encoding='utf-8-sig', errors='replace').read()

for eid in ('DOT_ControlProvince.10', 'DOT_ControlProvince.15'):
    m = re.search(r'news_event\s*=\s*\{[^{]*?id\s*=\s*' + re.escape(eid) + r'\b', t)
    if not m:
        print(f'{eid}: 未找到')
        continue
    start = m.start()
    depth, i, n = 0, t.find('{', start), len(t)
    while i < n:
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    print(f'===== {eid}（{i - start} 字节）=====')
    print(t[start:i + 1])
    print()

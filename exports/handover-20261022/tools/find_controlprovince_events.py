# -*- coding: utf-8 -*-
"""find_controlprovince_events.py —— 找 DOT_ControlProvince 新闻事件定义，检查 .10"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for base, tag in ((os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version'), 'gamma'),
                  (os.path.join(ROOT, 'Daybreak of Teyvat Beta Version'), 'beta')):
    print(f'=== {tag} ===')
    for p in glob.glob(os.path.join(base, 'events', '*.txt')):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        if 'DOT_ControlProvince' in t:
            ids = re.findall(r'(?m)^\s*(?:news_event|country_event)\s*=\s*\{\s*id\s*=\s*(DOT_ControlProvince\.\d+)', t)
            ids2 = re.findall(r'id\s*=\s*(DOT_ControlProvince\.\d+)', t)
            print(f'  {os.path.relpath(p, base)}: 定义 {sorted(set(ids2))}')
            # .10 的块
            m = re.search(r'(country_event|news_event)\s*=\s*\{[^{]*?id\s*=\s*DOT_ControlProvince\.10\b', t)
            if m:
                start = m.start()
                # 打前 800 字符
                print('  --- .10 定义 ---')
                print(t[start:start + 700])

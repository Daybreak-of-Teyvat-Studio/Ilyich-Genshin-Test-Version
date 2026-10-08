# -*- coding: utf-8 -*-
"""read_crash.py —— 读今早崩溃转储的 exception/meta/mods_registry"""
import os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
d = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\crashes\hoi4_20261008_093622'
for f in ('exception.txt', 'meta.yml'):
    p = os.path.join(d, f)
    print(f'=== {f} ===')
    t = open(p, encoding='utf-8', errors='replace').read()
    print(t[:1500] if t.strip() else '(空)')
p = os.path.join(d, 'mods_registry.json')
if os.path.exists(p):
    t = open(p, encoding='utf-8', errors='replace').read()
    print(f'=== mods_registry.json ({len(t)} 字节) ===')
    try:
        j = json.loads(t)
        print(json.dumps(j, ensure_ascii=False)[:1500])
    except Exception as e:
        print(t[:1500])

# -*- coding: utf-8 -*-
"""read_defaultmap.py —— 读 mod 与原版的 map/default.map（含字节级）"""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
STEAM = r'F:\Steam\steamapps\common\Hearts of Iron IV'

for name, base in (('mod', R), ('原版', STEAM)):
    p = os.path.join(base, 'map', 'default.map')
    print(f'=== {name}: {p} ===')
    if not os.path.exists(p):
        print('不存在')
        continue
    raw = open(p, 'rb').read()
    print('字节数:', len(raw))
    if len(raw) < 10:
        print('内容(hex):', raw.hex())
    else:
        t = raw.decode('utf-8-sig', errors='replace')
        # 只打 max_provinces 等关键行 + 前后各 20 行
        keys = [l for l in t.splitlines() if any(k in l for k in ('max_provinces', 'definitions', 'provinces', 'sea_starts', 'lakes'))]
        print('关键行:')
        for l in keys[:12]:
            print('  ', l.strip()[:120])
        print('前 25 行:')
        print('\n'.join('  ' + l for l in t.splitlines()[:25]))
    print()

print('=== system.log 尾部 20 行 ===')
p = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\system.log'
ls = [l.rstrip() for l in open(p, encoding='utf-8', errors='replace')]
print('\n'.join(l[:170] for l in ls[-20:]))

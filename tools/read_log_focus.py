# -*- coding: utf-8 -*-
"""read_log_mapfocus.py —— 精抽最新日志的地图类错误 + 尾部"""
import os, sys, re, collections

sys.stdout.reconfigure(encoding='utf-8')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]

STRICT = re.compile(r'(map\.cpp|mapbuildings|strategicair|MAP_ERROR|Map invalid|crossing|'
                    r'airports|rocketsites|supply_nodes|railways|adjacen|coastal|'
                    r'positions|unitstacks|strategic_region|continent|terrain|heightmap|'
                    r'no pixels|colou?r|definition)')
print('=== 地图类严格匹配 ===')
hits = [l.strip() for l in lines if STRICT.search(l)]
print(f'共 {len(hits)} 行:')
for l in hits[:120]:
    print('  ', l[:230])

print()
print('=== error.log 尾部 60 行 ===')
for l in lines[-60:]:
    print('  ', l.strip()[:230])

print()
print('=== 各时间段的错误行数（每 10 秒） ===')
c = collections.Counter()
for l in lines:
    m = re.match(r'^\[(\d{2}:\d{2}):(\d{2})\]', l)
    if m:
        c[f'{m.group(1)}:{int(m.group(2))//10*10:02d}'] += 1
for k in sorted(c):
    print(f'  {k}: {c[k]}')

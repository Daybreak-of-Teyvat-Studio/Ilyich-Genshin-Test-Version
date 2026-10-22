# -*- coding: utf-8 -*-
"""log_detail.py —— 从 error.log 抽关键错误的完整明细"""
import re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
t = open(P, 'rb').read().decode('utf-8-sig', errors='replace')
lines = t.split('\n')

def show(title, pat, limit=60):
    rx = re.compile(pat)
    hits = [l.strip() for l in lines if rx.search(l)]
    print(f'===== {title} ({len(hits)} 行) =====')
    seen = set()
    for l in hits[:limit]:
        print('  ', l[:240])
    if len(hits) > limit:
        print(f'   ... 还有 {len(hits)-limit} 行')
    print()

# 1) MAP_ERROR 全部州号
rx = re.compile(r'MAP_ERROR: no air base site defined for state (\d+)')
ids = sorted({int(m.group(1)) for l in lines for m in [rx.search(l)] if m})
print(f'===== MAP_ERROR no air base site: {len(ids)} 个州 =====')
print('  ', ids)
print()

show('no rocket site 州号', r'MAP_ERROR: no rocket site defined for state (\d+)', 5)
rx2 = re.compile(r'MAP_ERROR: no rocket site defined for state (\d+)')
ids2 = sorted({int(m.group(1)) for l in lines for m in [rx2.search(l)] if m})
print('  rocket ids:', ids2)
rx3 = re.compile(r'MAP_ERROR: no gun emplacement defined for state (\d+)')
ids3 = sorted({int(m.group(1)) for l in lines for m in [rx3.search(l)] if m})
print('  gun ids:', ids3)
print()

show('too many buildings', r'has too many buildings', 30)
show('Subunit is of support type', r'Subunit is of support type', 10)
show('LAW variant', r'LAW.*equipment variant|equipment variant.*LAW', 10)
show('sea_on_actions', r'14_sea_on_actions', 20)
show('State 1039 not found', r'not found', 20)
show('X crossing', r'X crossing', 5)

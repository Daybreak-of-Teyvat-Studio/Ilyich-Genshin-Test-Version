# -*- coding: utf-8 -*-
"""read_log_now.py —— 读用户最新一次运行的三份日志关键内容"""
import os, sys, re, collections

sys.stdout.reconfigure(encoding='utf-8')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'

print('=' * 70)
print('【game.log】全文')
p = os.path.join(L, 'game.log')
t = open(p, encoding='utf-8-sig', errors='replace').read()
for l in t.split('\n'):
    print('  ', l.rstrip()[:170])

print()
print('=' * 70)
print('【error.log】总览')
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]
print(f'  行数 {len(lines)}')

KW = re.compile(r'(?i)map|strateg|building|province|state|supply|railway|airport|rocket|adjacen|coastal|crossing|invalid|failed')
groups = collections.OrderedDict()
for l in lines:
    if not KW.search(l):
        continue
    m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l)
    ts2 = m.group(1) if m else '??'
    k = re.sub(r'\d+', '#', re.sub(r'\[\w+\.cpp:\d+\]', '[]', l.strip()))[:140]
    if k not in groups:
        groups[k] = [0, ts2, l.strip()[:230]]
    groups[k][0] += 1
print(f'  地图/州相关类 {len(groups)} 个（按首现时间）:')
for k, (n, ts2, sample) in sorted(groups.items(), key=lambda x: x[1][1]):
    print(f'  [首现 {ts2}] ×{n}')
    print(f'     {sample}')

print()
print('=' * 70)
print('【setup.log 尾部 40 行】')
t = open(os.path.join(L, 'setup.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]
for l in lines[-40:]:
    print('  ', l.rstrip()[:170])

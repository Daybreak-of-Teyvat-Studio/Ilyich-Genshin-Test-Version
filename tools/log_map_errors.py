# -*- coding: utf-8 -*-
"""log_map_errors.py —— 从 error.log 中抽取地图/州/省份相关错误并归类"""
import re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
t = open(P, 'rb').read().decode('utf-8-sig', errors='replace')

KW = re.compile(r'(?i)province|state|strateg|building|terra|supply|railway|adjacen|'
                r'coastal|continent|victory|capital|map\.|definition|provinces\.bmp|'
                r'id out of|out of bounds|invalid|does not exist|not found')

def norm(l):
    l = l.strip()
    l = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\[\w+\]', '', l)
    l = re.sub(r'\[\w+\.cpp:\d+\]', '[]', l)
    l = re.sub(r'\d+', '#', l)
    l = re.sub(r'"[^"]*"', '"..."', l)
    l = re.sub(r'\b[A-Z]{3}\b', 'TAG', l)
    return l[:150]

groups = collections.OrderedDict()
skipped = 0
for line in t.split('\n'):
    if not line.strip() or not KW.search(line):
        continue
    m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', line)
    ts = m.group(1) if m else '??'
    k = norm(line)
    if k not in groups:
        groups[k] = [0, ts, line.strip()[:220]]
    groups[k][0] += 1

print(f'=== 地图/州相关错误 {len(groups)} 类（按首次出现时间排序） ===\n')
for k, (n, ts, sample) in sorted(groups.items(), key=lambda x: x[1][1]):
    print(f'[首现 {ts}] ×{n}')
    print(f'  归类: {k}')
    print(f'  例:   {sample}')
    print()

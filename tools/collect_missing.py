# -*- coding: utf-8 -*-
"""collect_missing.py —— 完整收集：缺变体清单 + 名称占用清单 + 缺失 OOB 文件"""
import sys, re, collections

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()

print('=== 缺变体（country, type, version_name）===')
pat = re.compile(r'Country "(\w+)" does not have any equipment variant for type "([a-z_0-9]+)"(?: version_name "([^"]*)")?')
cnt = collections.Counter()
for l in ls:
    m = pat.search(l)
    if m:
        cnt[(m.group(1), m.group(2), m.group(3) or '(version 0)')] += 1
for k, v in sorted(cnt.items()):
    print(f'  {k[0]}: {k[1]}  version_name={k[2]}  ×{v}')

print()
print('=== 名称占用（The division name is occupied）===')
occ = collections.Counter()
for l in ls:
    m = re.search(r'The division name is occupied: (.+)$', l)
    if m:
        occ[m.group(1).strip()] += 1
for k, v in occ.most_common(20):
    print(f'  {k}: ×{v}')

print()
print('=== 缺失的 OOB 文件 ===')
miss = collections.Counter()
for l in ls:
    m = re.search(r'Could not open file: (history/units/\S+), error: not found', l)
    if m:
        miss[m.group(1)] += 1
for k, v in sorted(miss.items()):
    print(f'  {k} ×{v}')

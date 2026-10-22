# -*- coding: utf-8 -*-
"""control_test.py —— 对照实验
A) 48 个州文件的省份 vs definition.csv 存在性 + category 合法值
B) 10-04 崩溃转储日志中的 'Definition for state id' / 'Loaded N provinces' 对照
"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
IDS = [6, 7, 8, 9] + list(range(56, 100))

# definition 省集
dids = set()
for l in open(os.path.join(R, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if a[0].strip().isdigit():
        dids.add(int(a[0]))

print('=== A. 48 州内容检查 ===')
issues = []
for sid in IDS:
    p = os.path.join(R, 'history', 'states', f'{sid}-State_{sid}.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in pm.group(1).split()] if pm else []
    missing = [x for x in provs if x not in dids]
    cat = re.search(r'state_category\s*=\s*(\w+)', t)
    if missing:
        issues.append((sid, 'province 不在 definition', missing))
    if not provs:
        issues.append((sid, '空省份列表', None))
print(f'有问题的州: {len(issues)}')
for x in issues[:20]:
    print('  ', x)

# category 全集
cats = {}
for f in os.listdir(os.path.join(R, 'history', 'states')):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(R, 'history', 'states', f), encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'state_category\s*=\s*(\w+)', t)
    if m:
        cats[m.group(1)] = cats.get(m.group(1), 0) + 1
print('全 mod state_category 分布:', cats)

print()
print('=== B. 10-04 转储对照 ===')
CD = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\crashes\hoi4_20261004_214707\logs'
p = os.path.join(CD, 'error.log')
if os.path.exists(p):
    t = open(p, encoding='utf-8', errors='replace').read()
    print('10-04 error.log 行数:', len(t.splitlines()))
    print('  "Definition for state id":', len(re.findall(r'Definition for state id', t)))
    print('  "no strategic region":', len(re.findall(r'no strategic region', t)))
    print('  "has no state":', len(re.findall(r'has no state', t)))
    print('  "Missing State ID":', len(re.findall(r'Missing State ID', t)))
else:
    print('10-04 转储无 logs 目录')
p2 = os.path.join(CD, '..', 'hoi4_20261004_214707')
print('转储目录内容:', os.listdir(p2) if os.path.isdir(p2) else '无')

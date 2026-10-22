# -*- coding: utf-8 -*-
"""evidence2.py —— 三个被毁地图文件的语义还原"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')

print('=' * 70)
print('【A】beta airports.txt 全文分析（前 12 行 + 统计）')
tb = open(os.path.join(B, 'map', 'airports.txt'), encoding='utf-8-sig', errors='replace').read()
ls = [l for l in tb.split('\n') if l.strip()]
print(f'  总行数: {len(ls)}')
for l in ls[:12]:
    print('   ', l.rstrip())
ids = [int(m.group(1)) for l in ls for m in [re.match(r'\s*(\d+)=', l)] if m]
print(f'  州 id 范围: {min(ids)}-{max(ids)}, 共 {len(ids)} 个')
print(f'  是否含 709-750 海洋州: {sorted(x for x in ids if 700 <= x <= 760)}')

print()
print('=' * 70)
print('【B】beta rocketsites.txt 全文分析')
tb = open(os.path.join(B, 'map', 'rocketsites.txt'), encoding='utf-8-sig', errors='replace').read()
ls2 = [l for l in tb.split('\n') if l.strip()]
print(f'  总行数: {len(ls2)}')
for l in ls2[:8]:
    print('   ', l.rstrip())
ids2 = [int(m.group(1)) for l in ls2 for m in [re.match(r'\s*(\d+)=', l)] if m]
print(f'  州 id: {len(ids2)} 个, 范围 {min(ids2)}-{max(ids2)}')

print()
print('=' * 70)
print('【C】原版 + beta supply_nodes.txt 格式')
tv = open(os.path.join(V, 'map', 'supply_nodes.txt'), encoding='utf-8-sig', errors='replace').read()
lv = [l for l in tv.split('\n') if l.strip()]
print(f'  原版: {len(lv)} 行, 唯一首列州数: {len(set(l.split()[0] for l in lv))}')
for l in lv[:10]:
    print('   ', l.rstrip())
tb2 = open(os.path.join(B, 'map', 'supply_nodes.txt'), encoding='utf-8-sig', errors='replace').read()
lb = [l for l in tb2.split('\n') if l.strip()]
print(f'  beta: {len(lb)} 行, 唯一首列州数: {len(set(l.split()[0] for l in lb))}')
for l in lb[:10]:
    print('   ', l.rstrip())

print()
print('=' * 70)
print('【D】gamma buildings.txt 楼型分布 + air_base/supply_node/rocket 行样例')
bp = os.path.join(G, 'map', 'buildings.txt')
types = collections.Counter()
samples = collections.defaultdict(list)
state_of_prov = {}
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    if not l.strip():
        continue
    c = l.split(';')
    if len(c) < 7:
        continue
    t = c[1].strip()
    types[t] += 1
    if len(samples[t]) < 4:
        samples[t].append(l.strip())
print('  楼型计数:')
for t, n in types.most_common():
    print(f'    {t:28s} ×{n}')

print()
print('=' * 70)
print('【E】beta buildings.txt 楼型分布（对比）')
bp2 = os.path.join(B, 'map', 'buildings.txt')
types2 = collections.Counter()
if os.path.exists(bp2):
    for l in open(bp2, encoding='utf-8-sig', errors='replace'):
        if not l.strip():
            continue
        c = l.split(';')
        if len(c) >= 2:
            types2[c[1].strip()] += 1
    for t, n in types2.most_common():
        print(f'    {t:28s} ×{n}')
else:
    print('  beta buildings.txt 不存在')

print()
print('=' * 70)
print('【F】air_base 行样例（gamma）')
for l in samples.get('air_base', []):
    print('   ', l)
print('  原版 air_base 样例:')
cnt = 0
for l in open(os.path.join(V, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if ';air_base;' in l and cnt < 4:
        print('   ', l.strip())
        cnt += 1

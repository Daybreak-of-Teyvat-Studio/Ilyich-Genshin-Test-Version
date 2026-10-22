# -*- coding: utf-8 -*-
"""vanilla_sea_states.py —— 系统检查原版的"海州/含水域州"写法"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'

# 1) 原版 definition.csv kind 体系
kinds = {}
raw = open(os.path.join(V, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read()
for l in raw.split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            kinds[int(c[0])] = c[4]
        except ValueError:
            pass
print('=== 原版 definition.csv ===')
print(f'  省数 {len(kinds)}  kind 分布: {dict(collections.Counter(kinds.values()))}')
print(f'  头 3 行:')
for l in raw.split('\n')[:3]:
    print('   ', l.strip()[:100])

# 2) 原版所有州文件的省构成
print()
print('=== 原版州文件的水域构成 ===')
dist = collections.Counter()
examples = collections.defaultdict(list)
allsea = []
for f in glob.glob(os.path.join(V, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if not (m and m2):
        continue
    sid = int(m.group(1))
    ps = [int(x) for x in re.findall(r'\d+', m2.group(1))]
    ks = [kinds.get(p, '?') for p in ps]
    nl = ks.count('land')
    nw = len(ks) - nl          # 非陆地（sea/lake）
    key = 'all-land' if nw == 0 else ('all-water' if nl == 0 else 'mixed')
    dist[key] += 1
    if key != 'all-land' and len(examples[key]) < 8:
        examples[key].append((sid, os.path.basename(f), nl, nw, ps[:12]))
    if key == 'all-water':
        allsea.append((sid, os.path.basename(f)))
print(f'  分布: {dict(dist)}')
for key in ('all-water', 'mixed'):
    print(f'  --- {key} 例 ---')
    for sid, fn, nl, nw, ps in examples.get(key, []):
        print(f'    s{sid} {fn}: 陆{nl} 水{nw} 省样例={ps}')
print(f'  all-water 州总数: {len(allsea)}')
if allsea:
    print(f'    {allsea[:20]}')

# 3) 挑一个 all-water 州，看全文 + 它的 buildings.txt 行
if allsea:
    sid0 = allsea[0][0]
    print()
    print(f'=== all-water 州 s{sid0} 全文 ===')
    fs = glob.glob(os.path.join(V, 'history', 'states', f'{sid0}*.txt'))
    if fs:
        print(open(fs[0], encoding='utf-8-sig', errors='replace').read()[:1200])
    print(f'=== s{sid0} 在 buildings.txt 的行 ===')
    n = 0
    for l in open(os.path.join(V, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
        if l.startswith(f'{sid0};'):
            print('  ', l.strip()[:120])
            n += 1
    print(f'  共 {n} 行')

# 4) 再看一个 mixed 州的写法
if examples['mixed']:
    sid1 = examples['mixed'][0][0]
    print()
    print(f'=== mixed 州 s{sid1} 全文 ===')
    fs = glob.glob(os.path.join(V, 'history', 'states', f'{sid1}*.txt'))
    if fs:
        print(open(fs[0], encoding='utf-8-sig', errors='replace').read()[:1000])

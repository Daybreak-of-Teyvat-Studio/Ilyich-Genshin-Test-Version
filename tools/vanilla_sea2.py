# -*- coding: utf-8 -*-
"""vanilla_sea2.py —— ①混合州混的是 lake 还是 sea ②14_sea_on_actions 关键段 ③gamma 海省分布"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# ① 原版：混合州混的水域 kind
kinds = {}
for l in open(os.path.join(V, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read().split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            kinds[int(c[0])] = c[4]
        except ValueError:
            pass
cnt = collections.Counter()
in_state_water = collections.Counter()
for f in glob.glob(os.path.join(V, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m2:
        for p in [int(x) for x in re.findall(r'\d+', m2.group(1))]:
            k = kinds.get(p, '?')
            cnt[k] += 1
            if k in ('sea', 'lake'):
                in_state_water[k] += 1
print('=== 原版：所有州文件收录的省按 kind ===')
print(f'  {dict(cnt)}')
print(f'  被州收录的水域: {dict(in_state_water)}')
# 混合州里水省逐 kind 举例
print('  混合州中的具体水省 kind 抽样:')
shown = 0
for f in glob.glob(os.path.join(V, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m2:
        ps = [int(x) for x in re.findall(r'\d+', m2.group(1))]
        ws = [(p, kinds.get(p)) for p in ps if kinds.get(p) in ('sea', 'lake')]
        if ws and shown < 10:
            m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
            print(f'    s{m.group(1)}: {ws}')
            shown += 1

# ② 14_sea_on_actions 关键段
print()
print('=== 原版 14_sea_on_actions.txt 关键行 ===')
t = open(os.path.join(V, 'common', 'on_actions', '14_sea_on_actions.txt'), encoding='utf-8-sig', errors='replace').read()
ls = t.split('\n')
print(f'  总行数 {len(ls)}')
print('  --- 头 15 行 ---')
for l in ls[:15]:
    print('   ', l.rstrip()[:130])
for ln in (97, 196, 261):
    print(f'  --- 第 {ln} 行附近 ---')
    for l in ls[max(0, ln - 6):ln + 5]:
        print('   ', l.rstrip()[:130])

# ③ gamma：海省分布（在哪些州、无州多少）
print()
print('=== gamma：sea 省的去向 ===')
gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read().split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = c[4]
        except ValueError:
            pass
state_of = {}
sea_states = set()
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        sid = int(m.group(1))
        ps = [int(x) for x in re.findall(r'\d+', m2.group(1))]
        for p in ps:
            state_of[p] = sid
        if ps and all(gk.get(p) == 'sea' for p in ps):
            sea_states.add(sid)
sea_total = [p for p, k in gk.items() if k == 'sea']
in_sea_state = [p for p in sea_total if state_of.get(p) in sea_states]
in_land_state = [p for p in sea_total if p in state_of and state_of[p] not in sea_states]
no_state = [p for p in sea_total if p not in state_of]
print(f'  sea 省总数 {len(sea_total)}')
print(f'    ∈ 海洋州: {len(in_sea_state)}')
print(f'    ∈ 陆地州（混合）: {len(in_land_state)} 例: {[(p, state_of[p]) for p in in_land_state[:8]]}')
print(f'    不属于任何州: {len(no_state)}')
# 陆地省被并进海洋州的（反向混合）
land_in_sea = []
for s in sea_states:
    pass

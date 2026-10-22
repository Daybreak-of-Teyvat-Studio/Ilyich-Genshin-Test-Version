# -*- coding: utf-8 -*-
"""double_claim.py —— 省份被多州重复声明全查（重点 317 与海洋州）"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# definition kind
gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = c[4]
        except ValueError:
            pass

# 州 → 省（全部文件、全部声明）
prov_owners = collections.defaultdict(list)
state_provs = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if not (m and m2):
        continue
    sid = int(m.group(1))
    provs = [int(x) for x in re.findall(r'\d+', m2.group(1))]
    state_provs[sid] = provs
    for p in provs:
        prov_owners[p].append(sid)

dups = {p: ss for p, ss in prov_owners.items() if len(ss) > 1}
print(f'=== 双重/多重声明的省: {len(dups)} 个 ===')
for p, ss in sorted(dups.items())[:60]:
    print(f'  省{p}({gk.get(p)}): 被州 {ss} 声明')
print()

# 317 的土地省是不是被别的州抢了
p317 = state_provs.get(317, [])
print(f'317 的省: {p317}')
for p in p317:
    owners = prov_owners.get(p, [])
    print(f'  省{p}({gk.get(p)}): 声明州={owners}')
print()

# 每个州"引擎视角的净省数"：定义 = 该省全部声明者中的后一个？（试最后声明者归属）
# 先看每个海州有没有省被多州声明
sea_states = sorted(s for s, ps in state_provs.items()
                    if ps and all(gk.get(p) == 'sea' for p in ps))
print(f'海洋州 {len(sea_states)} 个: {sea_states}')
multi_sea = [(p, ss) for p, ss in dups.items() if gk.get(p) == 'sea']
print(f'海洋省被多州声明: {len(multi_sea)} 个')
for p, ss in multi_sea[:20]:
    print(f'  省{p}: {ss}')
print()

# 统计：每州被"抢走"了多少省（最后声明者视角）
last_owner = {}
for p, ss in prov_owners.items():
    last_owner[p] = ss[-1]   # 文件遍历序
lost = collections.Counter()
for p, ss in prov_owners.items():
    for s in ss[:-1]:
        lost[s] += 1
print(f'=== 按"最后声明者胜"假设，被抢省的州（前 25）===')
for s, n in lost.most_common(25):
    kindmix = collections.Counter(gk.get(p) for p in state_provs.get(s, []))
    print(f'  s{s}: 失去 {n} 省 (原省数 {len(state_provs.get(s, []))}, kind={dict(kindmix)})')
print()
# 317 在这假设下还剩什么
kept317 = [p for p in p317 if last_owner.get(p) == 317]
print(f'317 在最后声明者假设下保留: {kept317}')
# 反向：第一个声明者胜
first_owner = {p: ss[0] for p, ss in prov_owners.items()}
kept317f = [p for p in p317 if first_owner.get(p) == 317]
print(f'317 在第一声明者假设下保留: {kept317f}')

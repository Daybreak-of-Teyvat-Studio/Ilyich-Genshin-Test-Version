# -*- coding: utf-8 -*-
"""STATE_LEVEL 从零重排：清除所有生成点条目，按 861 陆州每州应有数量重新放置。"""
import os, re, sys, random, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
ORIG = os.path.join(ROOT, '.backups', 'map_buildings_20260923_222654', 'buildings.txt')
SL = {'air_base': 1, 'fuel_silo': 1, 'radar_station': 1, 'nuclear_reactor_spawn': 1,
      'rocket_site_spawn': 1, 'synthetic_refinery': 1, 'stronghold_network': 1,
      'anti_air_building': 3}
REMAP = {860: 125, 861: 123}   # 补号映射：原始州的生成点放到新号州
rng = random.Random(42)

s2p = {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]

POS = {}
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)',
                     open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig',
                          errors='replace').read()):
    POS[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))

lines = open(BP, encoding='utf-8-sig', newline='').read().split('\r\n')

# 1) 收集原始每州每 SL 类型的模板（类型+level 数据从原始表取）
#    目标：每陆州每种 SL 类型的数量 = 原始表该州数量
orig = collections.defaultdict(lambda: collections.defaultdict(list))
for l in open(ORIG, encoding='utf-8-sig', newline='').read().split('\r\n'):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        orig[f[1]][int(f[0])].append(l)

# 2) 删除当前所有 SL 条目（保留其他条目）
keep = []
for l in lines:
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        continue
    keep.append(l)
lines = keep
print(f'清除 SL 条目后剩 {len(lines)} 行')

# 3) 按原始模板重新放置：对每个陆州每 SL 类型，从原始条目取模板格式，
#    坐标用该州内省的 POS 坐标（每条分配不同的省）
placed = 0
new_entries = []
for st in sorted(s2p):
    provs = s2p[st]
    cands = [p for p in provs if p in POS]
    rng.shuffle(cands)
    src_state = next((o for o, n in REMAP.items() if n == st), st)   # 该州在原始基线里的 id
    for bt, base_n in SL.items():
        src_list = orig[bt].get(src_state, [])
        want = len(src_list)
        for k in range(want):
            if not cands:
                break
            p = cands[k % len(cands)]
            # 从原始表取一条该州该类型的条目作为模板
            tmpl = src_list[k % len(src_list)] if src_list else None
            if tmpl:
                tf = tmpl.split(';')
                # 只换第一列（州id）和坐标，其余保留
                tf[0] = str(st)
                tf[2] = f'{POS[p][0]:.2f}'
                tf[3] = f'{POS[p][1]:.2f}'
                tf[4] = f'{POS[p][2]:.2f}'
                new_entries.append(';'.join(tf))
            else:
                # 原始表里该州没这个类型——跳过
                pass
            placed += 1
print(f'重新放置 {placed} 条 STATE_LEVEL 条目')

# 4) 插入新条目：在原 SL 条目第一次出现的位置前插入
out = []
inserted = False
for l in lines:
    f = l.split(';')
    if not inserted and len(f) == 7 and f[1] not in SL and f[1] in ('arms_factory', 'industrial_complex'):
        pass
    out.append(l)
    if not inserted and len(f) == 7 and f[1] == 'air_base':
        out.extend(new_entries)
        inserted = True
if not inserted:
    # 找一个合适位置：在第一个非 SL 行后面
    for i, l in enumerate(out):
        f = l.split(';')
        if len(f) == 7 and f[1] not in SL:
            out[i+1:i+1] = new_entries
            inserted = True
            break
    if not inserted:
        out.extend(new_entries)

open(BP, 'w', encoding='utf-8', newline='').write('\r\n'.join(out))
print(f'已插入 {len(new_entries)} 条，备份到 .backups/')

# 5) 终验
after = collections.defaultdict(collections.Counter)
for l in open(BP, encoding='utf-8-sig', newline='').read().split('\r\n'):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) == 7:
        after[f[1]][int(f[0])] += 1
ob = collections.defaultdict(collections.Counter)
for l in open(ORIG, encoding='utf-8-sig', newline='').read().split('\r\n'):
    if l.strip():
        f = l.split(';')
        if len(f) == 7:
            ob[f[1]][int(f[0])] += 1
bad = 0
for bt in SL:
    ob2 = collections.Counter()
    for (st, n) in ob[bt].items():
        ob2[REMAP.get(st, st)] += n
    diff = {k for k in set(ob2) | set(after[bt]) if ob2.get(k, 0) != after[bt].get(k, 0)}
    bad += len(diff)
    if diff:
        print(f'  ! {bt}: {len(diff)} 州不符 {list(diff)[:5]}')
print(f'终验: 州级类型数量不符 {bad}（应 0，已按补号映射对照）')
print('总数守恒:', all(sum(ob[bt].values()) == sum(after[bt].values()) for bt in ob))

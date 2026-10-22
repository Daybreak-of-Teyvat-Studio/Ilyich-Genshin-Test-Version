# -*- coding: utf-8 -*-
"""evidence6.py —— 最后规则：行数vs等级 | 两条坏行 | 省id重合度 | beta文件细节"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')

# ---- A) 两条坏行原文 ----
print('=' * 70)
print('【A】buildings.txt 20325 / 38658 行原文')
bp = os.path.join(G, 'map', 'buildings.txt')
ls = open(bp, encoding='utf-8-sig', errors='replace').read().split('\n')
for ln in (20325, 38658):
    for i in range(ln - 3, ln + 2):
        mark = '>>>' if i == ln - 1 else '   '
        print(f'  {mark} L{i+1}: {ls[i][:110]}')
    print()

# ---- B) 每州每类型 行数 vs 州文件等级（s82/s76 vs 对照）----
print('=' * 70)
print('【B】每类型行数 vs 州文件等级')
def levels(base, sid):
    fs = glob.glob(os.path.join(base, 'history', 'states', f'{sid}*.txt'))
    fs = [f for f in fs if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    if not fs:
        return None
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'buildings\s*=\s*\{', t)
    if not m:
        return {}
    depth, i = 0, m.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    blk = t[m.end():i]
    lv = {}
    for bm in re.finditer(r'(?m)^\s*([a-z_]+)\s*=\s*(\d+)\s*$', blk):
        lv[bm.group(1)] = lv.get(bm.group(1), 0) + int(bm.group(2))
    return lv

rowcount = collections.defaultdict(collections.Counter)
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    if l.strip():
        c = l.split(';')
        if len(c) >= 2:
            rowcount[c[0].strip()][c[1].strip()] += 1

for s in (82, 76, 500, 607, 5, 400, 179, 600, 1, 177):
    lv = levels(G, s)
    rows = rowcount.get(str(s), {})
    print(f'  --- s{s} ---')
    for t in ('arms_factory', 'industrial_complex', 'dockyard', 'air_base', 'anti_air_building', 'radar_station'):
        print(f'      {t:22s} 行={rows.get(t,0):<3} 等级={lv.get(t,0) if lv else "?"}')
print()

# ---- C) beta 州1-3 的省列表 vs airports 选址 ----
print('=' * 70)
print('【C】beta 州 1/2/3 的省列表，验证选址在不在州内')
for sid, site in ((1, 1073), (2, 4405), (3, 2824)):
    fs = glob.glob(os.path.join(B, 'history', 'states', f'{sid}-*.txt')) or \
         glob.glob(os.path.join(B, 'history', 'states', f'{sid}(*.txt')) or \
         glob.glob(os.path.join(B, 'history', 'states', f'{sid}*.txt'))
    fs = [f for f in fs if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    if fs:
        t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        provs = [int(x) for x in re.findall(r'\d+', m.group(1))] if m else []
        print(f'   beta s{sid}: 选址={site} 在州内={site in provs} (州省数={len(provs)}, 前15省={provs[:15]})')
    else:
        print(f'   beta s{sid}: 文件未找到')
print()

# ---- D) 省 id 重合度：beta vs gamma ----
print('=' * 70)
print('【D】beta vs gamma 省 id 集合对比')
def defids(base):
    ids = {}
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        c = l.strip().split(';')
        if len(c) >= 5:
            try:
                ids[int(c[0])] = c[4]
            except ValueError:
                pass
    return ids
gi = defids(G)
bi = defids(B)
only_b = sorted(set(bi) - set(gi))
only_g = sorted(set(gi) - set(bi))
print(f'   beta 省数={len(bi)} gamma 省数={len(gi)}')
print(f'   仅 beta 有: {len(only_b)} 个 例: {only_b[:20]}')
print(f'   仅 gamma 有: {len(only_g)} 个 例: {only_g[:20]}')
print(f'   共有 id 中 kind 不同的: ', end='')
diff = [i for i in set(gi) & set(bi) if gi[i] != bi[i]]
print(f'{len(diff)} 个 例: {diff[:15]}')
print()

# ---- E) beta railways / supply_nodes 内容样例 ----
print('=' * 70)
print('【E】beta railways.txt 头 8 行 + supply_nodes 尾 5 行')
t = open(os.path.join(B, 'map', 'railways.txt'), encoding='utf-8-sig', errors='replace').read()
for l in [x for x in t.split('\n') if x.strip()][:8]:
    print('   ', l.rstrip()[:100])
print('   ---')
t = open(os.path.join(B, 'map', 'supply_nodes.txt'), encoding='utf-8-sig', errors='replace').read()
for l in [x for x in t.split('\n') if x.strip()][-5:]:
    print('   ', l.rstrip())
print()

# ---- F) beta 宫殿行 ----
print('=' * 70)
print('【F】beta buildings.txt 中 8 座宫殿行')
for l in open(os.path.join(B, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if 'Palace' in l:
        print('   ', l.strip())

# ---- G) 州号变动文档剩余部分（找海洋州段）----
print()
print('=' * 70)
print('【G】州号变动文档 40 行之后')
p = os.path.join(ROOT, 'docs', '州号变动_20261007至冬重划.md')
t = open(p, encoding='utf-8', errors='replace').read()
for l in t.split('\n')[40:80]:
    print('   ', l[:150])

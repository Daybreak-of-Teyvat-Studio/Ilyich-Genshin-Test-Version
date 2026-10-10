# -*- coding: utf-8 -*-
"""evidence5.py —— 317 全日志线 + 工业槽位对比 + 桥接资产结构 + 州号变动文档"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')

print('=' * 70)
print('【A】error.log 中所有含 "317" 的行')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
for l in open(P, encoding='utf-8-sig', errors='replace'):
    if ' 317' in l or '317 ' in l or '=317' in l or 'state 317' in l or '317}' in l:
        print('   ', l.strip()[:200])
print()

print('=' * 70)
print('【B】15 州 vs 对照州：工业等级/省数/行数/州文件细节')
INDU = ('arms_factory', 'industrial_complex', 'dockyard', 'anti_air_building',
        'synthetic_refinery', 'air_base')
bad = [76, 82, 223, 246, 269, 284, 311, 500, 560, 564, 569, 584, 587, 590, 607]
ctrl = [1, 5, 10, 50, 100, 150, 177, 179, 200, 300, 400, 450, 550, 600, 700]

def state_info(base, sid):
    fs = [f for f in glob.glob(os.path.join(base, 'history', 'states', f'{sid}*.txt'))
          if os.path.basename(f).startswith(str(sid) + '-') or os.path.basename(f).startswith(str(sid) + ' ')
          or os.path.basename(f) == f'{sid}.txt' or re.match(rf'^{sid}\(', os.path.basename(f))]
    if not fs:
        return None
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'buildings\s*=\s*\{', t)
    ind = {}
    blocks = []
    if m:
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
        for bm in re.finditer(r'(?m)^\s*([a-z_]+)\s*=\s*(\d+)\s*$', blk):
            ind[bm.group(1)] = ind.get(bm.group(1), 0) + int(bm.group(2))
        for bm in re.finditer(r'(?m)^\s*(\d+)\s*=\s*\{([^}]*)\}', blk):
            blocks.append((int(bm.group(1)), bm.group(2).strip()[:40]))
    prov = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    nprov = len(re.findall(r'\d+', prov.group(1))) if prov else 0
    cat = re.search(r'state_category\s*=\s*(\S+)', t)
    return dict(ind=ind, nprov=nprov, cat=cat.group(1) if cat else '?',
                prov_blocks=blocks, file=os.path.basename(fs[0]))

bp = os.path.join(G, 'map', 'buildings.txt')
rows = collections.Counter()
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    if l.strip():
        c = l.split(';')
        if len(c) >= 2:
            rows[c[0].strip()] += 1

print('  --- 报错的 15 州 ---')
for s in bad:
    info = state_info(G, s)
    if not info:
        print(f'  s{s}: 文件未找到!')
        continue
    indu_sum = sum(v for k, v in info['ind'].items() if k in INDU)
    print(f'  s{s:<4} 工业={indu_sum:<3} 省={info["nprov"]:<3} 行={rows.get(str(s),0):<4} 类别={info["cat"]:<6} 省块={info["prov_blocks"]} 全等级={info["ind"]}')
print()
print('  --- 对照（不报错）---')
for s in ctrl:
    info = state_info(G, s)
    if not info:
        print(f'  s{s}: 文件未找到!')
        continue
    indu_sum = sum(v for k, v in info['ind'].items() if k in INDU)
    print(f'  s{s:<4} 工业={indu_sum:<3} 省={info["nprov"]:<3} 行={rows.get(str(s),0):<4} 类别={info["cat"]:<6} 省块={info["prov_blocks"]}')
print()

print('=' * 70)
print('【C】原版州类别槽位（town/city/rural 等）')
for f in ('town.txt', 'rural.txt', 'city.txt', 'large_town.txt', 'megalopolis.txt'):
    p = os.path.join(V, 'common', 'state_category', f)
    if os.path.exists(p):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        slots = re.findall(r'(\w+)\s*=\s*\{\s*\n\s*local_building_slots\s*=\s*(\d+)', t)
        print(f'  {f}: {slots}')
# megalopolis gamma 覆盖
p = os.path.join(G, 'common', 'state_category', 'megalopolis.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
print(f'  gamma megalopolis: {re.findall(r"local_building_slots = (\\d+)", t)}')
print()

print('=' * 70)
print('【D】桥接资产结构')
for f in ('beta_gamma_bridge.json', 'zd_division.json', 'vp_live_dead.json', 'beta_gamma_manual_map.json'):
    p = os.path.join(ROOT, 'tools', f)
    if not os.path.exists(p):
        print(f'  {f}: 不存在')
        continue
    try:
        d = json.load(open(p, encoding='utf-8'))
        if isinstance(d, dict):
            ks = list(d.keys())[:6]
            print(f'  {f}: dict[{len(d)}] 键样例={ks}')
            for k in ks[:3]:
                v = d[k]
                vs = str(v)
                print(f'      {k!r} -> {vs[:120]}')
        else:
            print(f'  {f}: list[{len(d)}] 例={str(d[:3])[:150]}')
    except Exception as e:
        print(f'  {f}: 读取失败 {e}')
print()

print('=' * 70)
print('【E】docs/州号变动_20261007至冬重划.md 概要')
p = os.path.join(ROOT, 'docs', '州号变动_20261007至冬重划.md')
t = open(p, encoding='utf-8', errors='replace').read()
print(f'  长度 {len(t)} 字符')
for l in t.split('\n')[:40]:
    print('   ', l[:150])

# -*- coding: utf-8 -*-
"""evidence1.py —— 关键疑点取证：地图文件对比 + 超标建筑州 + 317 + SUM + LAW"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

# --- 1) 三个机场/火箭文件：原版 vs beta vs gamma vs 副本 ---
print('=' * 70)
print('【1】airports.txt / rocket_sites.txt / rocketsites.txt 对比')
for name in ('airports.txt', 'rocket_sites.txt', 'rocketsites.txt', 'supply_nodes.txt'):
    for tag, base in (('原版', V), ('beta', B), ('gamma仓库', G), ('gamma副本', D)):
        p = os.path.join(base, 'map', name)
        if os.path.exists(p):
            raw = open(p, 'rb').read()
            head = raw.decode('utf-8-sig', errors='replace').split('\n')[:3]
            print(f'  {name:18s} [{tag}] {len(raw):>8}B  头: {[h[:60] for h in head]}')
        else:
            print(f'  {name:18s} [{tag}] 不存在')
    print()

# --- 2) 15 个"too many buildings"州 ---
print('=' * 70)
print('【2】too many buildings 州：状态文件信息 + buildings.txt 计数')
bad = [76, 82, 223, 246, 269, 284, 311, 500, 560, 564, 569, 584, 587, 590, 607]
bp = os.path.join(D, 'map', 'buildings.txt')
bcount = collections.Counter()
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    if l.strip():
        bcount[l.split(';')[0].strip()] += 1
for sid in bad:
    fs = glob.glob(os.path.join(G, 'history', 'states', f'{sid}(*)*.txt')) or \
         glob.glob(os.path.join(G, 'history', 'states', f'{sid}-*.txt')) or \
         glob.glob(os.path.join(G, 'history', 'states', f'{sid} *.txt')) or \
         glob.glob(os.path.join(G, 'history', 'states', f'{sid}*.txt'))
    info = '文件未找到'
    if fs:
        t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
        nm = re.search(r'name\s*=\s*"([^"]*)"', t)
        cat = re.search(r'state_category\s*=\s*(\S+)', t)
        prov = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        nprov = len(re.findall(r'\d+', prov.group(1))) if prov else 0
        info = f"name={nm.group(1) if nm else '?'!r} cat={cat.group(1) if cat else '无'!r} prov={nprov}"
    print(f'  s{sid:<4} bld={bcount.get(str(sid), 0):<3} {info}  ← {os.path.basename(fs[0]) if fs else ""}')
print()

# --- 3) 317 州 ---
print('=' * 70)
print('【3】state 317 内容')
fs = glob.glob(os.path.join(G, 'history', 'states', '317*.txt'))
if fs:
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    print(f'  文件: {os.path.basename(fs[0])}')
    print('  ' + t[:600].replace('\n', '\n  '))
else:
    print('  317 文件未找到!')
print()

# --- 4) SUM_1936.txt 步兵编成（elephantry 上下文）---
print('=' * 70)
print('【4】SUM_1936.txt elephantry 出现处 (gamma vs beta)')
for tag, base in (('gamma', G), ('beta', B)):
    p = os.path.join(base, 'history', 'units', 'SUM_1936.txt')
    if os.path.exists(p):
        lines = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
        hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if 'elephantry' in l]
        print(f'  [{tag}] {len(hits)} 处:')
        for i, l in hits[:8]:
            print(f'    L{i}: {l[:80]}')
    else:
        print(f'  [{tag}] SUM_1936.txt 不存在')
print()

# --- 5) LAW 变体块 ---
print('=' * 70)
print('【5】LAW - Lawrence.txt 的变体块')
p = os.path.join(G, 'history', 'countries', 'LAW - Lawrence.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
for m in re.finditer(r'create_equipment_variant\s*=\s*\{', t):
    depth, i = 0, m.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    block = t[m.start():i + 1]
    print('  ---')
    for l in block.split('\n')[:14]:
        print('   ', l.rstrip()[:100])
    print()

# --- 6) 14_sea_on_actions.txt 在谁家 ---
print('=' * 70)
print('【6】14_sea_on_actions.txt 归属')
for tag, base in (('原版', V), ('beta', B), ('gamma副本', D)):
    p = os.path.join(base, 'common', 'on_actions', '14_sea_on_actions.txt')
    print(f'  {tag}: {"存在 " + str(os.path.getsize(p)) + "B" if os.path.exists(p) else "不存在"}')

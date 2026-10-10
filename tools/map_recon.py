# -*- coding: utf-8 -*-
"""map_recon.py —— gamma 地图目录侦察"""
import os, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

mp = os.path.join(G, 'map')
print('=== map/ 目录 ===')
for p in sorted(glob.glob(os.path.join(mp, '*'))):
    if os.path.isdir(p):
        sub = glob.glob(os.path.join(p, '*'))
        print(f'  [dir] {os.path.basename(p)}/  ({len(sub)} files)')
    else:
        print(f'  {os.path.basename(p):40s} {os.path.getsize(p):>10,} B')

# definition.csv
print('\n=== definition.csv ===')
dp = os.path.join(mp, 'definition.csv')
raw = open(dp, 'rb').read()
print(f'  size={len(raw):,}  BOM={raw[:3] == b"\xef\xbb\xbf"}')
text = raw.decode('utf-8-sig', errors='replace')
lines = text.split('\n')
print(f'  lines={len(lines)}  头3行/尾2行:')
for l in lines[:3]:
    print('   ', repr(l[:90]))
for l in lines[-2:]:
    print('   ', repr(l[:90]))

# 解析
ids, dup_ids, colors, dup_colors, malformed = set(), set(), {}, set(), []
kind_count = {}
for i, l in enumerate(lines):
    l = l.strip().rstrip('\r')
    if not l:
        continue
    parts = l.split(';')
    if len(parts) < 8:
        malformed.append((i + 1, l[:70]))
        continue
    try:
        pid = int(parts[0])
    except ValueError:
        malformed.append((i + 1, l[:70]))
        continue
    if pid in ids:
        dup_ids.add(pid)
    ids.add(pid)
    col = (parts[1], parts[2], parts[3])
    if col in colors:
        dup_colors.add(col)
    colors[col] = pid
    kind_count[parts[4]] = kind_count.get(parts[4], 0) + 1
print(f'  省份数={len(ids)}  id范围={min(ids)}-{max(ids)}')
print(f'  kind分布={kind_count}')
print(f'  重复id={len(dup_ids)} {sorted(dup_ids)[:10]}')
print(f'  重复颜色={len(dup_colors)} {sorted(dup_colors)[:5]}')
print(f'  畸形行={len(malformed)}')
for i, l in malformed[:10]:
    print(f'    L{i}: {l}')

# 战略区域
print('\n=== strategicregions ===')
sr = glob.glob(os.path.join(mp, 'strategicregions', '*.txt'))
print(f'  文件数={len(sr)}')
if sr:
    t = open(sr[0], 'rb').read().decode('utf-8-sig', errors='replace')
    print(f'  示例 {os.path.basename(sr[0])} 头12行:')
    for l in t.split('\n')[:12]:
        print('   ', l.rstrip()[:90])

# supply_nodes / railways / default.map
for f in ('supply_nodes.txt', 'railways.txt', 'default.map', 'continent.txt'):
    p = os.path.join(mp, f)
    if os.path.exists(p):
        t = open(p, 'rb').read().decode('utf-8-sig', errors='replace')
        n = len(t.split('\n'))
        print(f'\n=== {f} ({n} 行) 头8行 ===')
        for l in t.split('\n')[:8]:
            print('   ', l.rstrip()[:90])
    else:
        print(f'\n=== {f}: 不存在 ===')

# buildings.txt
bp = os.path.join(mp, 'buildings.txt')
if os.path.exists(bp):
    t = open(bp, 'rb').read().decode('utf-8-sig', errors='replace')
    ls = [l for l in t.split('\n') if l.strip()]
    print(f'\n=== buildings.txt ({len(ls)} 行非空) 头5行 ===')
    for l in ls[:5]:
        print('   ', l.rstrip()[:90])

# state 文件数
st = glob.glob(os.path.join(G, 'history', 'states', '*.txt'))
print(f'\n=== history/states: {len(st)} 个文件 ===')

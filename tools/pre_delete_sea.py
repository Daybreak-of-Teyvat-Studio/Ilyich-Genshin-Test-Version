# -*- coding: utf-8 -*-
"""pre_delete_sea.py —— 删除海州前的安全扫描（只读）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

SEA = set(range(709, 718)) | set(range(719, 751))
SEA_S = {str(x) for x in SEA}

print('=== ① common/events/history 中对 709-750 的 state 语法引用 ===')
PAT = re.compile(r'((?:state|owns_state|controls_state|transfer_state|state_id)\s*=\s*)(\d+)(?!\d)')
n = 0
for sub in ('common', 'events', 'history'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        if 'states' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if 'resource_prospecting' in rel or '14_sea_on_actions' in rel or '12_wuw' in rel:
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for i, l in enumerate(t.split('\n')):
                for m in PAT.finditer(l):
                    if m.group(2) in SEA_S:
                        print(f'  {rel} L{i+1}: {l.strip()[:120]}')
                        n += 1
print(f'  共 {n} 处')

print()
print('=== ② 裸作用域 N = { 形式 ===')
n = 0
for sub in ('common', 'events'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if 'resource_prospecting' in rel or '14_sea_on_actions' in rel or '12_wuw' in rel:
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for i, l in enumerate(t.split('\n')):
                m = re.match(r'\s*(\d+)\s*=\s*\{', l)
                if m and m.group(1) in SEA_S:
                    print(f'  {rel} L{i+1}: {l.strip()[:110]}')
                    n += 1
print(f'  共 {n} 处')

print()
print('=== ③ unitstacks.txt 首列是否为州号（抽样）===')
p = os.path.join(G, 'map', 'unitstacks.txt')
first_cols = set()
cnt = 0
for l in open(p, encoding='utf-8-sig', errors='replace'):
    c = l.split(';')
    if c and c[0].strip().isdigit():
        first_cols.add(int(c[0]))
        cnt += 1
        if cnt > 60000:
            break
mx = max(first_cols) if first_cols else 0
print(f'  首列样例 {sorted(first_cols)[:12]}... 最大 {mx}  (若是州号应≤750)')
sea_in = [v for v in first_cols if v in SEA]
print(f'  首列 ∈ 海州段的数量: {len(sea_in)} 例: {sorted(sea_in)[:12]}')

print()
print('=== ④ airports/rocketsites 中海州行 ===')
for f in ('airports.txt', 'rocketsites.txt', 'supply_nodes.txt'):
    p = os.path.join(G, 'map', f)
    n = 0
    for l in open(p, encoding='utf-8-sig', errors='replace'):
        m = re.search(r'^\s*(\d+)', l)
        if m and m.group(1) in SEA_S:
            n += 1
    print(f'  {f}: {n} 行')

print()
print('=== ⑤ loc 键与 bookmarks/首都 抽查 ===')
n = sum(1 for sid in SEA if True)
print(f'  海州 loc 键范围 709-750（保留死键，无害）')
for bf in glob.glob(os.path.join(G, 'common', 'bookmarks', '*.txt')):
    t = open(bf, encoding='utf-8-sig', errors='replace').read()
    hits = [m.group(0) for m in re.finditer(r'\b(7\d\d)\b', t) if m.group(1) in SEA_S]
    if hits:
        print(f'  ★ {os.path.basename(bf)}: {hits[:10]}')
print('  （无输出 = bookmarks 干净）')

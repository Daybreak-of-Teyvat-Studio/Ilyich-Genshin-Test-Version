# -*- coding: utf-8 -*-
"""scan_ownerless2.py —— 双副本对比扫描：无 owner / 无 core / 无 buildings / 空省份"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]

kind = {}
for l in open(os.path.join(COPIES[0][1], 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        kind[int(a[0])] = a[4]

for tag, base in COPIES:
    ST = os.path.join(base, 'history', 'states')
    fs = sorted(glob.glob(os.path.join(ST, '*.txt')))
    n_ownerless_land, n_empty, n_nocore_owned = [], [], []
    for f in fs:
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        provs = [int(x) for x in (pm.group(1).split() if pm else [])]
        land_n = sum(1 for p in provs if kind.get(p) == 'land')
        om = re.search(r'\bowner\s*=\s*(\w+)', t)
        cores = re.findall(r'add_core_of\s*=\s*(\w+)', t)
        if not provs:
            n_empty.append(sid)
        if not om and land_n > 0:
            n_ownerless_land.append((sid, land_n))
        if om and not cores:
            n_nocore_owned.append(sid)
    print(f'=== {tag}: 文件 {len(fs)} 个 ===')
    print(f'  空省份州: {len(n_empty)} {n_empty[:20]}')
    print(f'  含陆地但无 owner: {len(n_ownerless_land)} {n_ownerless_land[:20]}')
    print(f'  有 owner 无 core: {len(n_nocore_owned)} {n_nocore_owned[:20]}')

# 文件名/id 不一致、重复 id
print()
for tag, base in COPIES:
    ST = os.path.join(base, 'history', 'states')
    ids = []
    mis = []
    for f in sorted(glob.glob(os.path.join(ST, '*.txt'))):
        fn = os.path.basename(f)
        m = re.match(r'(\d+)-', fn)
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        c = re.search(r'\bid\s*=\s*(\d+)', t)
        if m and c:
            ids.append(int(c.group(1)))
            if int(m.group(1)) != int(c.group(1)):
                mis.append(fn)
    dup = [x for x in set(ids) if ids.count(x) > 1]
    print(f'{tag}: id 范围 {min(ids)}-{max(ids)}，文件名/id 不一致 {len(mis)}，重复 id {len(dup)} {dup[:10]}')

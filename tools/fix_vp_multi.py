# -*- coding: utf-8 -*-
"""修复 4 个州的双 VP 覆盖：重写为多省一行格式"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

FIX = {133: [(4649, 25), (4651, 15)],
       130: [(707, 15), (1327, 10)],
       129: [(2106, 5), (4640, 15)],
       859: [(2363, 5), (2274, 15)]}

bdir = os.path.join(ROOT, '.backups', 'vp_multi_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
for sid, vps in FIX.items():
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = open(fp, encoding='utf-8-sig', newline='').read()
    line = 'victory_points = { ' + ' '.join(f'{p} {v}' for p, v in vps) + ' }'
    t = re.sub(r'victory_points\s*=\s*\{[^}]*\}', line, t, count=1)
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)
    m = re.search(r'victory_points\s*=\s*\{([^}]*)\}', t)
    print(f'  state {sid}: {m.group(0)}')

# 全 mod VP 复验
tot, multi_bad = [], 0
p2s = {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for m in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        v = m.group(1).split()
        pairs = list(zip(v[0::2], v[1::2]))
        for a, b in pairs:
            tot.append((int(a), int(b)))
            if not b.isdigit():
                multi_bad += 1
print(f'\n全 mod VP {len(tot)} 个（{len(tot)} 条值，格式异常 {multi_bad}）')
print('本次新增/相关:', [t for t in tot if t[0] in (4556, 680, 881, 1485, 4698, 4649, 4651, 707, 1327, 2106, 4640, 2363, 2274, 4614, 4668)])
print(f'备份 {bdir}')

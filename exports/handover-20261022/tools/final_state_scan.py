# -*- coding: utf-8 -*-
"""final_state_scan.py —— 全量扫描两类错误的残余（全 750 州，不依赖日志）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')

coastal = {}
for l in open(os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map', 'definition.csv'),
              encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 6 and a[0].strip().isdigit() and int(a[0]) > 0:
        coastal[int(a[0])] = (a[5].strip().lower() == 'true')

bad_dy, bad_blk = [], []
for f in sorted(glob.glob(os.path.join(ST, '*.txt'))):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in (pm.group(1).split() if pm else [])]
    pset = set(provs)
    coast = [p for p in provs if coastal.get(p)]
    bm = re.search(r'buildings\s*=\s*\{', t)
    if not bm:
        continue
    depth, i = 0, bm.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    block = t[bm.start():i + 1]
    # 1) coastal-only 州级建筑无海岸
    for b in ('dockyard', 'naval_base', 'naval_base_spawn', 'naval_headquarters',
              'naval_supply_hub', 'floating_harbor', 'coastal_bunker'):
        if re.search(r'(?m)^\s*' + b + r'\s*=\s*\d+', block) and not coast:
            bad_dy.append((sid, b))
    # 2) 省级块引用不在本州的省
    for m in re.finditer(r'(?m)^\s*(\d+)\s*=\s*\{', block):
        pid = int(m.group(1))
        if pid not in pset:
            bad_blk.append((pid, sid))

print(f'残余① coastal 建筑无海岸: {len(bad_dy)} {bad_dy[:15]}')
print(f'残余② 省级块错州: {len(bad_blk)} {bad_blk[:15]}')
print('全部干净 ✓' if not bad_dy and not bad_blk else '（见上）')

# -*- coding: utf-8 -*-
"""SL 超配物理删除：每陆州保留 7×1 + anti_air×3，多余删除"""
import os, re, sys, shutil, collections, datetime
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
SL = {'air_base': 1, 'fuel_silo': 1, 'radar_station': 1, 'nuclear_reactor_spawn': 1,
      'rocket_site_spawn': 1, 'synthetic_refinery': 1, 'stronghold_network': 1,
      'anti_air_building': 3}

s2o = {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    s2o[sid] = mo.group(1) if mo else None

raw = open(BP, 'rb').read()
nl = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl)
seen = collections.Counter()
out, removed = [], 0
for l in lines:
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        st = int(f[0])
        seen[(f[1], st)] += 1
        if s2o.get(st) is None or seen[(f[1], st)] > SL[f[1]]:
            removed += 1
            continue
    out.append(l)
open(BP, 'w', encoding='utf-8', newline='').write(nl.join(out))
print(f'删除超配/无效 SL 条目 {removed} 条')

after = collections.defaultdict(lambda: collections.defaultdict(int))
for l in open(BP, encoding='utf-8-sig', newline='').read().split(nl):
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        after[f[1]][int(f[0])] += 1
bad = 0
for bt in SL:
    for st, own in s2o.items():
        want = 0 if own is None else SL[bt]
        if after[bt].get(st, 0) != want:
            bad += 1
print(f'终验: SL 数量不符 {bad}（应 0）')

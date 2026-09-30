# -*- coding: utf-8 -*-
"""删除海州（无 owner 的州）的州级生成点条目——海州不该有 SL 生成点"""
import os, re, sys, shutil, collections, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
ORIG = os.path.join(ROOT, '.backups', 'map_buildings_20260923_222654', 'buildings.txt')
SL = {'air_base', 'fuel_silo', 'radar_station', 'nuclear_reactor_spawn',
      'rocket_site_spawn', 'synthetic_refinery', 'stronghold_network', 'anti_air_building'}

sea = set()
s2o = {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    if not mo:
        sea.add(sid)
print(f'海州 {len(sea)} 个')

raw = open(BP, 'rb').read()
lines = raw.decode('utf-8-sig').split('\r\n')
out, removed = [], 0
for l in lines:
    f = l.split(';')
    if len(f) == 7 and f[1] in SL and f[0].isdigit() and int(f[0]) in sea:
        removed += 1
        continue
    out.append(l)
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(BP, os.path.join(ROOT, '.backups', f'buildings_before_seaSL_{stamp}.txt'))
open(BP, 'w', encoding='utf-8', newline='').write('\r\n'.join(out))
print(f'删除海州 SL 条目 {removed} 条')

# 终验
after = collections.defaultdict(collections.Counter)
for l in open(BP, encoding='utf-8-sig', newline='').read().split('\r\n'):
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        after[f[1]][int(f[0])] += 1
ob = collections.defaultdict(collections.Counter)
for l in open(ORIG, encoding='utf-8-sig', newline='').read().split('\r\n'):
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        ob[f[1]][int(f[0])] += 1
REMAP = {860: 125, 861: 123}
bad = 0
for bt in SL:
    ob2 = collections.Counter()
    for st, n in ob[bt].items():
        if st in (123, 125):
            continue                    # 被删空州：份额已随省转移消失
        ob2[REMAP.get(st, st)] += n
    diff = {k for k in set(ob2) | set(after[bt]) if ob2.get(k, 0) != after[bt].get(k, 0)}
    bad += len(diff)
    if diff:
        print(f'  ! {bt}: {len(diff)} 州 {list(diff)[:5]}')
print(f'终验: 生成点不符 {bad}（应 0）')
n_sl = sum(1 for l in open(BP, encoding='utf-8-sig', newline='').read().split('\r\n')
           if l.split(';')[1:2] and l.split(';')[1] in SL)
print(f'当前 SL 总条目 {n_sl}（基线 8610 − 被删空州 2×10 = 8590）')

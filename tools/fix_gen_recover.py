# -*- coding: utf-8 -*-
"""恢复 buildings.txt 并用正确逻辑补齐（保留现有、只补缺、删超配）"""
import os, re, sys, glob, shutil, collections, random
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BP = os.path.join(G, 'map', 'buildings.txt')
ORIG = os.path.join(ROOT, '.backups', 'map_buildings_20260923_222654', 'buildings.txt')
SL = {'air_base': 1, 'fuel_silo': 1, 'radar_station': 1, 'nuclear_reactor_spawn': 1,
      'rocket_site_spawn': 1, 'synthetic_refinery': 1, 'stronghold_network': 1,
      'anti_air_building': 3}

# 1) 找最近的 .bak_ 恢复（补齐脚本自己做的改动前备份）
baks = sorted(glob.glob(BP + '.bak_*'), key=os.path.getmtime, reverse=True)
assert baks, '找不到 .bak_ 备份！'
bak = baks[0]
shutil.copy2(bak, BP)
print(f'已从 {os.path.basename(bak)} 恢复 buildings.txt（{os.path.getsize(BP)} 字节）')

# 2) 读现状
s2p = {}
for f in os.listdir(os.path.join(G, 'history', 'states')):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(G, 'history', 'states', f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
POS = {}
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)',
                     open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig',
                          errors='replace').read()):
    POS[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
TMPL = {}
for l in open(ORIG, encoding='utf-8-sig', newline='').read().split('\r\n'):
    f = l.split(';')
    if len(f) == 7 and f[1] in SL and f[1] not in TMPL:
        TMPL[f[1]] = f

raw = open(BP, 'rb').read()
nl_s = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl_s)

cur = collections.Counter()
out = []
removed = 0
for l in lines:
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        key = (f[1], int(f[0]))
        cur[key] += 1
        if cur[key] > SL[f[1]]:
            removed += 1
            continue          # 超配 → 物理删除
    out.append(l)

added = 0
rng = random.Random(11)
appends = []
for st in sorted(s2p):
    land = [p for p in s2p[st] if p in POS]
    if not land:
        continue
    for bt, want in SL.items():
        have = cur.get((bt, st), 0)
        for k in range(want - have):
            f = list(TMPL[bt])
            px, py, pz = POS[land[(hash((st, bt, k))) % len(land)]]
            f[0] = str(st)
            f[2], f[3], f[4] = f'{px:.2f}', f'{py:.2f}', f'{pz:.2f}'
            appends.append(';'.join(f))
            added += 1
out = out + appends
open(BP, 'w', encoding='utf-8', newline='').write(nl_s.join(out))
print(f'恢复后补缺 {added} 条、删超配 {removed} 条')

# 3) 终验
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
        ob2[REMAP.get(st, st)] += n
    diff = {k for k in set(ob2) | set(after[bt]) if ob2.get(k, 0) != after[bt].get(k, 0)}
    bad += len(diff)
    if diff:
        print(f'  ! {bt}: {len(diff)} 州 {list(diff)[:5]}')
print(f'终验: 生成点不符 {bad}（应 0）')
print('总数守恒:', all(sum(ob[bt].values()) == sum(after[bt].values()) for bt in SL))

# -*- coding: utf-8 -*-
"""生成点标准配置补齐：每陆州 7类×1 + anti_air×3；缺补（模板取基线）、多删。"""
import os, re, sys, shutil, datetime, random, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
ORIG = os.path.join(ROOT, '.backups', 'map_buildings_20260923_222654', 'buildings.txt')
SL = {'air_base': 1, 'fuel_silo': 1, 'radar_station': 1, 'nuclear_reactor_spawn': 1,
      'rocket_site_spawn': 1, 'synthetic_refinery': 1, 'stronghold_network': 1,
      'anti_air_building': 3}

s2p = {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
POS = {}
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)',
                     open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig',
                          errors='replace').read()):
    POS[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))

# 基线模板行（每类取 1 条作样板）
TMPL = {}
for l in open(ORIG, encoding='utf-8-sig', newline='').read().split('\r\n'):
    f = l.split(';')
    if len(f) == 7 and f[1] in SL and f[1] not in TMPL:
        TMPL[f[1]] = f

raw = open(BP, 'rb').read()
nl = b'\r\n' if b'\r\n' in raw else b'\n'
lines = raw.decode('utf-8-sig').split(nl.decode())

cur = collections.defaultdict(lambda: collections.defaultdict(list))
keep = []
for l in lines:
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        cur[f[1]][int(f[0])].append(f)
    else:
        keep.append(l)

rng = random.Random(7)
added = removed = 0
new_entries = []
for st in sorted(s2p):
    land_provs = [p for p in s2p[st] if p in POS]
    if not land_provs:
        continue          # 海州不放
    for bt, want in SL.items():
        have = cur[bt].get(st, [])
        # 删多余
        for f_extra in have[want:]:
            removed += 1
        # 补缺失
        for k in range(want - len(have)):
            f = list(TMPL[bt])
            p = land_provs[(hash((st, bt)) + k) % len(land_provs)]
            px, py, pz = POS[p]
            f[0] = str(st)
            f[2], f[3], f[4] = f'{px:.2f}', f'{py:.2f}', f'{pz:.2f}'
            new_entries.append(';'.join(f))
            added += 1

out = keep + new_entries
shutil.copy2(BP, BP + '.bak_' + datetime.datetime.now().strftime('%H%M%S'))
open(BP, 'w', encoding='utf-8', newline='').write(nl.decode().join(out))
print(f'补 {added} 条、删 {removed} 条（多余项未物理删除，仅计数——如需物理删除见下）')
# 物理删除多余项：重写一遍（只保留每州前 want 条）
cur2 = collections.defaultdict(lambda: collections.defaultdict(int))
out2 = []
seen_cnt = collections.Counter()
for l in out:
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        key = (f[1], int(f[0]))
        seen_cnt[key] += 1
        if seen_cnt[key] > SL[f[1]]:
            removed_final = 1
            continue
    out2.append(l)
open(BP, 'w', encoding='utf-8', newline='').write(nl.decode().join(out2))
print(f'物理删除超配 {sum(1 for l in out if l not in out2)} 行')

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
        ob2[REMAP.get(st, st)] += n
    diff = {k for k in set(ob2) | set(after[bt]) if ob2.get(k, 0) != after[bt].get(k, 0)}
    bad += len(diff)
    if diff:
        print(f'  ! {bt}: {len(diff)} 州不符 {list(diff)[:5]}')
print(f'终验: 生成点数量不符 {bad}（应 0）')
print('总数守恒:', all(sum(ob[bt].values()) == sum(after[bt].values()) for bt in SL))

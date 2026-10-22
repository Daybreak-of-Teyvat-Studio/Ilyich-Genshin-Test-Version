# -*- coding: utf-8 -*-
"""
守门检查：map/buildings.txt 相比「原始文件」的不变量。

  1. 州级生成点：每州数量必须与原始完全一致（这轮崩溃就是它被破坏）
  2. 没有州级生成点为 0 的州
  3. 行数 / CRLF / 无 BOM
  4. 每一行的字段数都是 7
"""
import os, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BP = os.path.join(G, 'map', 'buildings.txt')
ORIG = os.path.join(ROOT, '.backups', 'map_buildings_20260923_222654', 'buildings.txt')
STATE_LEVEL = {'air_base', 'fuel_silo', 'radar_station', 'nuclear_reactor_spawn',
               'rocket_site_spawn', 'synthetic_refinery', 'stronghold_network',
               'anti_air_building'}


def load(p):
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8')
    cnt = collections.defaultdict(collections.Counter)
    nf = 0
    for l in t.split('\r\n'):
        if not l.strip():
            continue
        f = l.split(';')
        if len(f) != 7:
            nf += 1
            continue
        cnt[f[1]][int(f[0])] += 1
    return raw, t, cnt, nf


rb, tb, cb, nfb = load(ORIG)
ra, ta, ca, nfa = load(BP)
LF = bytes([10])
CRLF = bytes([13, 10])
BOM = bytes([239, 187, 191])
print(f'原始 {len(rb)} 字节 / 现在 {len(ra)} 字节')
print(f'行数 原始 {rb.count(CRLF)} / 现在 {ra.count(CRLF)}')
print(f'纯 CRLF 原始 {rb.count(LF) == rb.count(CRLF)} / 现在 {ra.count(LF) == ra.count(CRLF)}')
print(f'BOM 原始 {rb[:3] == BOM} / 现在 {ra[:3] == BOM}')
print(f'字段数异常 原始 {nfb} / 现在 {nfa}')

print()
bad = 0
for bt in sorted(STATE_LEVEL):
    diff = {k: (cb[bt].get(k, 0), ca[bt].get(k, 0))
            for k in set(cb[bt]) | set(ca[bt]) if cb[bt].get(k, 0) != ca[bt].get(k, 0)}
    print(f'{bt:28s} 原始州数 {len(cb[bt]):4d} 现在 {len(ca[bt]):4d} 数量不符的州 {len(diff)}')
    for k, v in list(diff.items())[:8]:
        print(f'      州 {k}: {v[0]} -> {v[1]}')
    bad += len(diff)
allstates = set()
for bt in cb:
    allstates |= set(cb[bt])
miss = [s for s in sorted(allstates) if any(ca[bt].get(s, 0) == 0 for bt in STATE_LEVEL)]
print()
print(f'州级类型数量不符的 (州,类型) 数: {bad}  {"✓ 与原始一致" if bad == 0 else "✗"}')
print(f'缺州级生成点的州: {len(miss)} 个 {miss[:20]}')
print()
print('各类型总数: 原始 -> 现在')
for bt in sorted(cb, key=lambda x: -sum(cb[x].values())):
    o, n = sum(cb[bt].values()), sum(ca[bt].values())
    mark = '' if o == n else f'   {"+" if n > o else ""}{n-o}'
    print(f'  {bt:32s} {o:6d} -> {n:6d}{mark}')

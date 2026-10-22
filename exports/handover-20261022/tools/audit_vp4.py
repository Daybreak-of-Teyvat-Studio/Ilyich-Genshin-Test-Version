# -*- coding: utf-8 -*-
"""audit_vp4.py —— 审计 4 条 VP（1343迪弗旧窟/4216桓摩洞/1416雨的尽头/1442晴雨的经纬）
并全库搜这四个名字，看是否也有错挂残留"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
LOC = os.path.join(MOD, 'localisation')
ITEMS = [(1343, '迪弗旧窟', 15), (4216, '桓摩洞', 15), (1416, '雨的尽头', 15), (1442, '晴雨的经纬', 15)]

p2s, vps_of = {}, {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        p2s[int(x)] = sid
    vv = {}
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        xs = vm.group(1).split()
        for i in range(0, len(xs) - 1, 2):
            vv[int(xs[i])] = int(xs[i + 1])
    if vv:
        vps_of[sid] = vv

vpn = {}
for p in glob.glob(os.path.join(LOC, '**', '*.yml'), recursive=True):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s+"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        vpn[int(m.group(1))] = m.group(2)

for pid, nm, val in ITEMS:
    h = p2s.get(pid)
    cur = vps_of.get(h, {}).get(pid)
    ok = cur == val and vpn.get(pid) == nm
    print(f'p{pid}「{nm}」{val}: 在 s{h}；state VP={cur}；本地化「{vpn.get(pid)}」 -> {"✓" if ok else "✗"}')

print()
print('=== 四个名字全库搜索（找错挂残留） ===')
for p in glob.glob(os.path.join(LOC, '**', '*.yml'), recursive=True):
    rel = os.path.relpath(p, LOC)
    for i, l in enumerate(open(p, encoding='utf-8-sig', errors='replace').read().splitlines(), 1):
        m = re.match(r'^\s*((?:DOT_STATE|VICTORY_POINTS)_\d+):\d*\s+"([^"]*)"', l)
        if m and any(nm in m.group(2) for _, nm, _ in ITEMS):
            print(f'  {rel}:{i}  {m.group(1)} = "{m.group(2)}"')

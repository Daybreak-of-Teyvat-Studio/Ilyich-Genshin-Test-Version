# -*- coding: utf-8 -*-
"""recon_1314b.py —— 补查：s266/s433 的 VP 条目、loc 历史、真实脚本引用"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMMA = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(GAMMA, 'history', 'states')

print('=== 1. s266 / s433 的 VP 条目 ===')
for sid in (266, 433):
    t = open(os.path.join(ST, f'{sid}-State_{sid}.txt'), encoding='utf-8-sig', errors='replace').read()
    nm = re.search(r'name\s*=\s*"([^"]*)"', t)
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    vps = re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', t)
    print(f'  s{sid}: owner={om.group(1) if om else "海"} name={nm.group(1) if nm else "?"} VP={vps}')

print()
print('=== 2. loc 里的 1314 / 442 ===')
for p in glob.glob(os.path.join(GAMMA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(1314|442):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        print(f'  {os.path.basename(p)}: VICTORY_POINTS_{m.group(1)} = "{m.group(2)}"')

print()
print('=== 3. 备份历史里的这两个 key ===')
for bd in sorted(glob.glob(os.path.join(ROOT, '.backups', '*'))) + \
          sorted(glob.glob(os.path.join(ROOT, 'Daybreak of Teyvat Beta Version', '.backups', '*'))):
    vpf = glob.glob(os.path.join(bd, 'DOT_Victory_Points*.yml'))
    for p in vpf:
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        a = re.search(r'VICTORY_POINTS_1314:\d*\s*"([^"]*)"', t)
        b = re.search(r'VICTORY_POINTS_442:\d*\s*"([^"]*)"', t)
        print(f'  {os.path.relpath(bd, ROOT)}: 1314={a.group(1) if a else "无"}, 442={b.group(1) if b else "无"}')

print()
print('=== 4. 脚本真实引用（排除 map/备份/坐标）===')
n = 0
for root, dirs, files in os.walk(GAMMA):
    dirs[:] = [d for d in dirs if d not in ('.backups', '.backup', '.git', 'map', 'localisation', 'history')]
    for f in files:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(root, f)
        rr = os.path.relpath(p, GAMMA).replace('\\', '/')
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        for i, l in enumerate(t.splitlines(), 1):
            if re.search(r'(?<![.\d])1314(?![.\d])', l):
                n += 1
                if n <= 40:
                    print(f'  [{rr}:{i}] {l.strip()[:110]}')
print(f'  共 {n} 行')
# history 目录里也查（国家历史/州文件）
print()
print('=== 5. history/ 下 1314 的引用（非 state 文件）===')
n2 = 0
for root, dirs, files in os.walk(os.path.join(GAMMA, 'history')):
    for f in files:
        if not f.endswith('.txt') or f.startswith(('1-', '2-', '3-', '4-', '5-', '6-', '7-', '8-', '9-')):
            continue
        p = os.path.join(root, f)
        rr = os.path.relpath(p, GAMMA).replace('\\', '/')
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        for i, l in enumerate(t.splitlines(), 1):
            if re.search(r'(?<![.\d])1314(?![.\d])', l):
                n2 += 1
                if n2 <= 20:
                    print(f'  [{rr}:{i}] {l.strip()[:110]}')
print(f'  共 {n2} 行')

# -*- coding: utf-8 -*-
"""precheck_natlan_fix.py —— 修复前置检查：目标州 VP 现状 / 游离 VP 值 / 旧 VP key"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')

print('=== 目标州现有 VP 块 ===')
for sid in (747, 722, 782, 735, 707):
    f = os.path.join(ST, f'{sid}-State_{sid}.txt')
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    vps = re.findall(r'victory_points\s*=\s*\{([^}]*)\}', t)
    print(f'  s{sid}: ' + (' | '.join(' '.join(v.split()) for v in vps) if vps else '(无)'))

print()
print('=== 游离 VP 值检查（4484/4356/4484 等） ===')
for pid in (4484, 4356):
    for f in glob.glob(os.path.join(ST, '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        for v in re.findall(r'victory_points\s*=\s*\{([^}]*)\}', t):
            xs = v.split()
            for i in range(0, len(xs) - 1, 2):
                if int(xs[i]) == pid:
                    print(f'  p{pid} 在 s{sid} 有 VP 值 {xs[i+1]}')

print()
print('=== 目标省所在州确认 ===')
p2s = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        p2s[int(x)] = sid
for pid in (2149, 1482, 4338):
    print(f'  p{pid} -> s{p2s.get(pid)}')

print()
print('=== 旧 VP 本地化 key 检查 ===')
vpf = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
for m in re.finditer(r'^\s*(VICTORY_POINTS_(?:2149|1482|4338|389|4154|4484|4356)):\d*\s+"([^"]*)"',
                     open(vpf, encoding='utf-8-sig', errors='replace').read(), re.M):
    print(f'  {m.group(1)} = "{m.group(2)}"')

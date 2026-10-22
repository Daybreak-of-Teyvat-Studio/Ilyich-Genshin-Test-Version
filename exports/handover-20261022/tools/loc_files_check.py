# -*- coding: utf-8 -*-
"""loc_files_check.py —— 两个 state_names 文件的分工与 VP 键分布"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'localisation', 'simp_chinese')

for fn in sorted(os.listdir(G)):
    if not fn.endswith('.yml'):
        continue
    p = os.path.join(G, fn)
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    n_state = len(re.findall(r'(?m)^\s*DOT_STATE_\d+:', t))
    n_vp = len(re.findall(r'(?m)^\s*VICTORY_POINTS_\d+:', t))
    n_old_state = len(re.findall(r'(?m)^\s*STATE_\d+:', t))
    if n_state or n_vp or n_old_state or 'state_names' in fn or 'Victory' in fn:
        print(f'{fn}: DOT_STATE {n_state}, VICTORY_POINTS {n_vp}, 旧式 STATE_ {n_old_state}, {os.path.getsize(p)//1024}KB')

print()
p = os.path.join(G, 'DOT_state_names_l_simp_chinese.yml')
if os.path.exists(p):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print('=== DOT_state_names_l 头部 15 行 ===')
    print('\n'.join(t.splitlines()[:15]))
    vps = re.findall(r'(?m)^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"', t)
    print(f'其中 VICTORY_POINTS 键 {len(vps)} 个')
    print('样例:', vps[:10])
    print('含 1314:', [x for x in vps if x[0] == '1314'])

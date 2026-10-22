# -*- coding: utf-8 -*-
"""find_true_states.py —— 用英文名键找六个名字的"正主"州"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

KEYS = ['Shirikoro_Peak', 'Moshiri_Ceremonial_Site', 'Musoujin_Gorge', 'Serpent_Mine',
        'Bourou_Village', 'Amakumo', 'Tsurumi', 'Yashiori', 'Watatsumi', 'Seirai']

print('=== 州文件里引用这些英文键的 ===')
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    nm = re.search(r'(?m)^\s*name\s*=\s*"([^"]*)"', t)
    ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
    for k in KEYS:
        if k in t:
            print(f'  {os.path.basename(f)}: id={m.group(1) if m else "?"} name键={nm.group(1) if nm else "-"} owner={ow.group(1) if ow else "-"} 含[{k}]')
            break

print()
print('=== 六个英文键在 loc 里的完整条目 ===')
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    for k in ['Shirikoro_Peak', 'Moshiri_Ceremonial_Site', 'Musoujin_Gorge', 'Serpent_Mine', 'Bourou_Village']:
        for mm in re.finditer(rf'(?m)^\s*{k}\s*:\s*(\d*)\s*"([^"]*)"', t):
            print(f'  [{os.path.basename(f)}] {k}:{mm.group(1)} = {mm.group(2)}')

print()
print('=== DOT_state_names_l 中 Shirikoro_Peak 周边 40 行（看岛屿名字块）===')
p = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_l_simp_chinese.yml')
if os.path.exists(p):
    ls = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
    for i, l in enumerate(ls):
        if 'Shirikoro_Peak' in l:
            for j in range(max(0, i - 20), min(len(ls), i + 20)):
                print(f'  L{j+1}: {ls[j][:100]}')
            break

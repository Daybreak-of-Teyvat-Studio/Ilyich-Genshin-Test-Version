# -*- coding: utf-8 -*-
"""check_lyy_scraps.py —— LYY 碎州(原89/90/94)的省份 3958/4689/4690 现属哪个州"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

WANT = {3958, 4689, 4690}
print('=== 省 3958/4689/4690 现属州 ===')
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        ps = set(int(x) for x in re.findall(r'\d+', m2.group(1)))
        hit = WANT & ps
        if hit:
            print(f'  {os.path.basename(f)} (id={m.group(1)}): 含 {sorted(hit)}')

print()
print('=== 当前各州尾部（695-706）速览 ===')
for f in sorted(glob.glob(os.path.join(G, 'history', 'states', '*State_*.txt'))):
    b = os.path.basename(f)
    m = re.match(r'(\d+)-', b)
    if m and 695 <= int(m.group(1)) <= 706:
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
        m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        ps = [int(x) for x in re.findall(r'\d+', m2.group(1))] if m2 else []
        print(f'  {b}: owner={ow.group(1) if ow else "-"} 省{len(ps)}')

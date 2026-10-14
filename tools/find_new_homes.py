# -*- coding: utf-8 -*-
"""find_new_homes.py —— 搜当前 states 里注释为 STATE_707/708/709 的文件 = 新家"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== 当前 states 里的 # name="STATE_70X" 注释 ===')
for f in sorted(glob.glob(os.path.join(G, 'history', 'states', '*.txt'))):
    head = open(f, encoding='utf-8-sig', errors='replace').read()[:400]
    for was in ('706', '707', '708', '709'):
        if f'name="STATE_{was}"' in head:
            t = open(f, encoding='utf-8-sig', errors='replace').read()
            ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
            man = re.search(r'manpower\s*=\s*(\d+)', t)
            m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
            ps = [int(x) for x in re.findall(r'\d+', m2.group(1))] if m2 else []
            print(f'  原号{was} → 现住 {os.path.basename(f)}: owner={ow.group(1) if ow else "-"} man={man.group(1) if man else "-"} 省{len(ps)}')

print()
print('=== 昨晚 23:43 被动过的所有文件的注释速览 ===')
import time
d = os.path.join(G, 'history', 'states')
rows = []
for f in os.listdir(d):
    p = os.path.join(d, f)
    mt = os.path.getmtime(p)
    if mt > time.mktime(time.strptime('2026-10-13 20:00:00', '%Y-%m-%d %H:%M:%S')):
        rows.append((mt, f))
rows.sort(reverse=True)
for mt, f in rows:
    t = open(os.path.join(d, f), encoding='utf-8-sig', errors='replace').read()
    nm = re.search(r'(?m)^\s*name\s*=\s*"([^"]*)"([^\n]*)', t)
    ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
    print(f'  {time.strftime("%m-%d %H:%M", time.localtime(mt))} {f}: owner={ow.group(1) if ow else "-"} | {(nm.group(0).strip() if nm else "-")[:70]}')

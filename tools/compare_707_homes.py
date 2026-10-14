# -*- coding: utf-8 -*-
"""compare_707_homes.py —— 对比备份(10-07)里的 707/708/709/89/90/94 与当前"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BK = os.path.join(ROOT, '.backups', 'states_20261007_231638', 'history', 'states')

def brief(p, tag):
    if not os.path.exists(p):
        print(f'  [{tag}] {os.path.basename(p)}: 不存在')
        return
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    nm = re.search(r'(?m)^\s*name\s*=\s*"([^"]*)"([^\n]*)', t)
    ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
    man = re.search(r'manpower\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    ps = [int(x) for x in re.findall(r'\d+', m2.group(1))] if m2 else []
    print(f'  [{tag}] {os.path.basename(p)}: {(nm.group(0).strip() if nm else "-")[:74]}')
    print(f'        owner={ow.group(1) if ow else "-"} man={man.group(1) if man else "-"} 省{len(ps)}: {ps[:8]}')

print('=== 10-07 备份 ===')
for sid in (89, 90, 94, 706, 707, 708, 709):
    found = glob.glob(os.path.join(BK, f'{sid}-*.txt'))
    for p in found:
        brief(p, '备份10-07')

print()
print('=== 当前（10-14）===')
for sid in (89, 90, 94, 706):
    found = glob.glob(os.path.join(G, 'history', 'states', f'{sid}-*.txt'))
    for p in found:
        brief(p, '当前')

print()
print('=== 备份(10-07) 里 89/90/94 的省 vs 当前 707/708/709 内容对照 ===')
print('(707/708/709 的 10-07 内容若 == 当前 89/90/94，说明那是三对同一内容的迁移)')

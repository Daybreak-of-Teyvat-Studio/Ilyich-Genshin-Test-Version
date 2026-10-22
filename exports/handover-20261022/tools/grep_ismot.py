# -*- coding: utf-8 -*-
"""grep_ismot.py —— Is_MOT 触发器定义检查 + 日志扫描"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== Is_MOT 在 mod 中的定义 ===')
for p in glob.glob(os.path.join(G, 'common', 'scripted_triggers', '*.txt')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'^\s*(Is_MOT|is_MOT|is_mot)\s*=\s*\{', t, re.M):
        s = m.start()
        print(f'  {os.path.basename(p)}: 定义于偏移 {s}')
        print('   ', t[s:s + 200].replace(chr(10), ' | ')[:200])
print('  （无输出 = 未定义？）')

print()
print('=== 全 mod 搜 Is_MOT 使用 ===')
cnt = 0
for dp, dn, fn in os.walk(G):
    dn[:] = [d for d in dn if d not in ('.backups', '.backup', '备份')]
    for f in fn:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(dp, f)
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        n = t.count('Is_MOT')
        if n:
            cnt += n
            print(f'  {os.path.relpath(p, G)}: {n} 处')
print(f'  共 {cnt} 处')

print()
print('=== error.log 中 Is_MOT / 433 / 442 / DVA 相关 ===')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
for i, l in enumerate(open(P, encoding='utf-8', errors='replace'), 1):
    if 'Is_MOT' in l or ('DVA' in l and 'organization' not in l and 'error.log' not in l):
        print(f'  {i}: {l.rstrip()[:160]}')

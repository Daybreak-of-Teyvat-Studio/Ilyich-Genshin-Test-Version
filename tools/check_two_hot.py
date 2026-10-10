# -*- coding: utf-8 -*-
"""check_two_hot.py —— 除零触发器 + PRI 海军 OOB 诊断"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== 1. NewMOT_scripted_triggers.txt 500-530 行 ===')
p = os.path.join(G, 'common', 'scripted_triggers', 'NewMOT_scripted_triggers.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read().splitlines()
for i in range(495, min(535, len(t))):
    print(f'  {i+1}: {t[i].rstrip()[:130]}')

print()
print('=== 全文件中 divide_temp_variable 的所有出现（找除数）===')
for i, l in enumerate(t, 1):
    if 'divide_temp_variable' in l:
        print(f'  {i}: {l.strip()[:140]}')

print()
print('=== 2. PRI_1936_Naval.txt 前 40 行 ===')
p = os.path.join(G, 'history', 'units', 'PRI_1936_Naval.txt')
print('  文件存在:', os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0, 'B')
if os.path.exists(p):
    t = open(p, encoding='utf-8-sig', errors='replace').read().splitlines()
    for i, l in enumerate(t[:40], 1):
        print(f'  {i}: {l.rstrip()[:130]}')

print()
print('=== 对照：一个正常的海军 OOB（DVA_1936_naval.txt 前 20 行）===')
p2 = os.path.join(G, 'history', 'units', 'DVA_1936_naval.txt')
t2 = open(p2, encoding='utf-8-sig', errors='replace').read().splitlines()
for i, l in enumerate(t2[:20], 1):
    print(f'  {i}: {l.rstrip()[:130]}')

print()
print('=== PRI 是否还有陆军 OOB / VAN 海军文件 ===')
for f in ('PRI_1936.txt', 'VAN_1936_naval.txt', 'VAN_1936.txt'):
    fp = os.path.join(G, 'history', 'units', f)
    print(f'  {f}: {"存在 " + str(os.path.getsize(fp)) + "B" if os.path.exists(fp) else "不存在"}')

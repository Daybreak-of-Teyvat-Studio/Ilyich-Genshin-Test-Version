# -*- coding: utf-8 -*-
"""check_new_errors.py —— LYY 事件语法错 + 全日志 parse/scope 类错误 + OOB 重复检查"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== 1. 日志中所有 Unexpected token / Invalid scope / Error: 行（12:50 会话）===')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()
for i, l in enumerate(ls, 1):
    if 'Unexpected token' in l or 'Invalid scope' in l or ('Error:' in l and 'near line' in l):
        print(f'  {i}: {l[:200]}')

print()
print('=== 2. LYY_Keqing_Events.txt 问题区域（85-100 行）===')
p = os.path.join(G, 'events', 'LYY_Keqing_Events.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read().splitlines()
for i in range(84, min(100, len(t))):
    print(f'  {i+1}: {t[i].rstrip()[:130]}')

print()
print('=== 3. LYY_Ganyu_Events.txt 第 2580 行附近 ===')
p = os.path.join(G, 'events', 'LYY_Ganyu_Events.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read().splitlines()
for i in range(2570, min(2590, len(t))):
    print(f'  {i+1}: {t[i].rstrip()[:130]}')

print()
print('=== 4. history/units 每 tag 的 OOB 文件（查重复）===')
files = collections.defaultdict(list)
for f in glob.glob(os.path.join(G, 'history', 'units', '*.txt')):
    b = os.path.basename(f)
    tag = b.split('_')[0]
    files[tag].append(b)
for tag, fs in sorted(files.items()):
    if len(fs) > 1:
        print(f'  {tag}: {fs}')

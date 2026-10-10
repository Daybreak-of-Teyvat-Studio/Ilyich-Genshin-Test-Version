# -*- coding: utf-8 -*-
"""beta_pri_check.py —— beta 的 PRI 舰名唯一性 + VAN 海军文件内容"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== beta PRI_1936_Naval.txt 舰名分析 ===')
p = os.path.join(B, 'history', 'units', 'PRI_1936_Naval.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
names = re.findall(r'ship = \{ name = "([^"]+)"', t)
c = collections.Counter(names)
print(f'  舰数 {len(names)}，唯一名 {len(c)}')
print('  最高频:', c.most_common(8))

print()
print('=== gamma PRI_1936_Naval.txt 舰名分析 ===')
p = os.path.join(G, 'history', 'units', 'PRI_1936_Naval.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
names = re.findall(r'ship = \{ name = "([^"]+)"', t)
c = collections.Counter(names)
print(f'  舰数 {len(names)}，唯一名 {len(c)}')
print('  最高频:', c.most_common(8))

print()
print('=== beta VAN_1936_naval.txt 全文 ===')
p = os.path.join(B, 'history', 'units', 'VAN_1936_naval.txt')
print(repr(open(p, 'rb').read()))

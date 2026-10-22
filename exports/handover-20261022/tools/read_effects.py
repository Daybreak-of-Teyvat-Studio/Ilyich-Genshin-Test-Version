# -*- coding: utf-8 -*-
"""read_effects.py —— 读 DOT_SRD_Develop_Rate_Ice 决策的完整效果块 + 统计该文件所有建筑类效果"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

p = os.path.join(G, 'common', 'decisions', 'DOT_Resources.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
ls = t.split('\n')

# 找 DOT_SRD_Develop_Rate_Ice 的块（从 L1110 起到下一个决策前）
print('=== DOT_SRD_Develop_Rate_Ice 完整块（L1110-1220）===')
for i in range(1109, min(len(ls), 1220)):
    print(f'  L{i+1}: {ls[i].rstrip()[:125]}')

print()
print('=== 该文件里所有建筑类效果行 ===')
for i, l in enumerate(ls):
    if re.search(r'add_building_construction|add_extra_state_shared_building_slots|set_building_level', l):
        print(f'  L{i+1}: {l.strip()[:125]}')

print()
print('=== 该文件里的裸作用域数字块（N = { 形式）===')
for i, l in enumerate(ls):
    m = re.match(r'\s*(\d+)\s*=\s*\{', l)
    if m:
        print(f'  L{i+1}: {l.strip()[:110]}')

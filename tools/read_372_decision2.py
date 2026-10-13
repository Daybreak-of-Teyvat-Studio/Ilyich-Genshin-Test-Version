# -*- coding: utf-8 -*-
"""read_372_decision.py —— 372 州全文 + 浪船决策块全文"""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== 372 州全文 ===')
p = os.path.join(G, 'history', 'states', '372-State_372.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
print(t[:1600])

print('=== SUM_Repair_Ormos_Waverider 决策块（L239-345）===')
p2 = os.path.join(G, 'common', 'decisions', 'SUM_decisions.txt')
ls = open(p2, encoding='utf-8-sig', errors='replace').read().split('\n')
for i in range(238, min(len(ls), 345)):
    print(f'  L{i+1}: {ls[i].rstrip()[:125]}')

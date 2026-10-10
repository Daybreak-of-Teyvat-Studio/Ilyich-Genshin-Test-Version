# -*- coding: utf-8 -*-
"""diff_2refs.py —— 看 KNA_decision / INA_Focus 的换位联动内容"""
import sys, difflib

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
for rel in ('common/decisions/KNA_decision.txt', 'common/national_focus/INA_Focus.txt'):
    rp = R + '\\' + rel.replace('/', '\\')
    dp = D + '\\' + rel.replace('/', '\\')
    a = open(dp, encoding='utf-8-sig', errors='replace').read().splitlines()
    b = open(rp, encoding='utf-8-sig', errors='replace').read().splitlines()
    print(f'=== {rel}（副本=前 → 仓库=后）===')
    for x in difflib.unified_diff(a, b, lineterm='', n=3):
        print(x[:150])
    print()

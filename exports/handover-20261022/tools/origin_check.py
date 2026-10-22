# -*- coding: utf-8 -*-
"""origin_check.py —— 区分引用文件是原版还是 mod 自有"""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
files = ['decisions/resource_prospecting.txt', 'decisions/DOT_Resources.txt', 'decisions/KNA_decision.txt',
         'decisions/VAN_decisions.txt', 'national_focus/FAV_FocusTree_01.txt', 'national_focus/LAW_FocusTree_02.txt',
         'national_focus/NewMOT_FocusTree_00.txt', 'scripted_triggers/VAN_scripted_triggers.txt',
         'scripted_effects/LYY_scripted_effects.txt', 'on_actions/ANR_influence_on_actions.txt',
         'ideas/DRA_andrius_manufacture.txt']
for f in files:
    p = os.path.join(V, 'common', *f.split('/'))
    print(('原版有  ' if os.path.exists(p) else '原版无★（mod自有）'), f)

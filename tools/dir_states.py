# -*- coding: utf-8 -*-
"""dir_states.py —— 列 states 目录全部 700 段文件"""
import os, sys, re, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
d = os.path.join(G, 'history', 'states')

fs = sorted(os.listdir(d))
print(f'总文件数: {len(fs)}')
print('700 段文件名:')
for f in fs:
    if re.match(r'7[0-1][0-9]', f):
        print('  ', f)
print()
print('末尾 15 个文件:', fs[-15:])

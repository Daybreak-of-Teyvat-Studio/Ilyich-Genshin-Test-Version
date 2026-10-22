# -*- coding: utf-8 -*-
"""read_crash2.py —— 看转储 dlc_load / 唯一 strategicregions 文件 / system.log 地图加载段"""
import os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
D = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
CD = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\crashes\hoi4_20261008_093622'

print('=== 转储 dlc_load.json ===')
p = os.path.join(CD, 'dlc_load.json')
print(open(p, encoding='utf-8', errors='replace').read() if os.path.exists(p) else '无')

print()
print('=== 转储 settings.txt（前 60 行）===')
p = os.path.join(CD, 'settings.txt')
t = open(p, encoding='utf-8', errors='replace').read()
print('\n'.join(t.splitlines()[:60]))

print()
print('=== map/strategicregions 唯一文件 ===')
SR = os.path.join(D, 'map', 'strategicregions')
fs = os.listdir(SR)
print(fs)
if fs:
    p = os.path.join(SR, fs[0])
    t = open(p, encoding='utf-8', errors='replace').read()
    print('大小', len(t), '字节，前 800 字符:')
    print(t[:800])
    print('...')
    # 统计 region 数与省引用数
    import re
    print('region 块数:', len(re.findall(r'(?m)^\s*\d+\s*=\s*\{', t)))
    print('province 列表元素数:', len(re.findall(r'\b\d+\b', t)))

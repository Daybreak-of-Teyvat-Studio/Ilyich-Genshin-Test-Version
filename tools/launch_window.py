# -*- coding: utf-8 -*-
"""launch_window.py —— 拉 23:10:40-23:11:00 载入窗口全部原始行"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()

print('===== 23:10:38 - 23:11:05 原始行 =====')
n = 0
for l in t.split('\n'):
    m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l)
    if m and '23:10:38' <= m.group(1) <= '23:11:05':
        print('  ', l.strip()[:240])
        n += 1
print(f'（{n} 行）')

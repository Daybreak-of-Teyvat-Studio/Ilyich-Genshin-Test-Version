# -*- coding: utf-8 -*-
"""raw_window.py —— 打印 error.log 指定窗口原始行（不去重）"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
lines = t.split('\n')

def show(w1, w2, title):
    print(f'===== {title} ({w1}-{w2}) =====')
    n = 0
    for l in lines:
        m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l)
        if m and w1 <= m.group(1) <= w2:
            print('  ', l.strip()[:235])
            n += 1
    print(f'  （{n} 行）')
    print()

show('22:51:22', '22:51:25', 'gameitemdatabase 8 errors 窗口')
show('22:51:33', '22:51:37', '历史后 / 地标错误窗口')

# -*- coding: utf-8 -*-
"""read_crash_now.py —— 读最新一次失败运行的日志"""
import os, re, sys, datetime, collections

sys.stdout.reconfigure(encoding='utf-8')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV'
print('=== 时间戳 ===')
for f in ('error.log', 'game.log'):
    p = os.path.join(D, 'logs', f)
    print(f'  {f}: {datetime.datetime.fromtimestamp(os.path.getmtime(p))} ({os.path.getsize(p)}B)')
cr = os.path.join(D, 'crashes')
print('  转储:', sorted(os.listdir(cr))[-3:] if os.path.isdir(cr) else '无')

print()
print('=== game.log ===')
print(open(os.path.join(D, 'logs', 'game.log'), encoding='utf-8', errors='replace').read())

print('=== error.log 尾部 40 行 ===')
ls = open(os.path.join(D, 'logs', 'error.log'), encoding='utf-8', errors='replace').read().splitlines()
print(f'（共 {len(ls)} 行）')
for l in ls[-40:]:
    print(l[:180])

print()
print('=== 最后 200 行中 State Error / 致命类 ===')
for l in ls[-400:]:
    if 'State Error' in l or 'Invalid' in l or 'invalid' in l or 'Failed' in l or 'failed' in l:
        print(' ', l[:180])

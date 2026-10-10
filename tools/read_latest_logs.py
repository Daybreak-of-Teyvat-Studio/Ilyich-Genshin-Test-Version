# -*- coding: utf-8 -*-
"""read_latest_logs.py —— 昨天两次运行的日志 + dockyard 线索"""
import os, re, sys, datetime, glob

sys.stdout.reconfigure(encoding='utf-8')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV'

print('=== 日志时间戳 ===')
for f in ('error.log', 'game.log', 'system.log'):
    p = os.path.join(D, 'logs', f)
    print(f'  {f}: {datetime.datetime.fromtimestamp(os.path.getmtime(p))} ({os.path.getsize(p)}B)')
print('=== 崩溃转储 ===')
cr = os.path.join(D, 'crashes')
fs = sorted(os.listdir(cr), key=lambda f: os.path.getmtime(os.path.join(cr, f)))
for f in fs[-4:]:
    print(f'  {f}: {datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(cr, f)))}')

print()
print('=== game.log 全文 ===')
print(open(os.path.join(D, 'logs', 'game.log'), encoding='utf-8', errors='replace').read())

print('=== error.log 尾部 30 行 ===')
ls = open(os.path.join(D, 'logs', 'error.log'), encoding='utf-8', errors='replace').read().splitlines()
print(f'（共 {len(ls)} 行）')
for l in ls[-30:]:
    print(l[:170])

print()
print('=== error.log 中 dockyard / invalid state building 相关 ===')
for i, l in enumerate(ls, 1):
    if 'dockyard' in l or 'invalid state building' in l or 'State Error' in l:
        print(f'  {i}: {l[:170]}')

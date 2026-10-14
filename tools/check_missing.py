# -*- coding: utf-8 -*-
"""check_missing.py —— 707/708/709 何时消失/去哪了"""
import os, re, sys, glob, time

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

print('=== ① 两副本 states 文件数 ===')
for tag, base in (('仓库', G), ('副本', D)):
    fs = os.listdir(os.path.join(base, 'history', 'states'))
    print(f'  {tag}: {len(fs)} 个')

print()
print('=== ② 仓库 states 目录最近修改的 15 个文件 ===')
d = os.path.join(G, 'history', 'states')
rows = [(os.path.getmtime(os.path.join(d, f)), f) for f in os.listdir(d)]
rows.sort(reverse=True)
for mt, f in rows[:15]:
    print(f'  {time.strftime("%m-%d %H:%M:%S", time.localtime(mt))}  {f}')

print()
print('=== ③ 707/708/709 内容是否在别处（搜 分道誓约之地/回声之子 的 state 文件）===')
for kw in ('分道誓约之地', '回声之子', 'DOT_STATE_708', 'DOT_STATE_709', 'DOT_STATE_707'):
    hits = []
    for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        if kw in t:
            hits.append(os.path.basename(f))
    print(f'  "{kw}": {hits[:5]}')

print()
print('=== ④ 最近的备份目录 ===')
bd = os.path.join(ROOT, '.backups')
if os.path.isdir(bd):
    rows = [(os.path.getmtime(os.path.join(bd, x)), x) for x in os.listdir(bd)]
    rows.sort(reverse=True)
    for mt, x in rows[:10]:
        print(f'  {time.strftime("%m-%d %H:%M:%S", time.localtime(mt))}  {x}')

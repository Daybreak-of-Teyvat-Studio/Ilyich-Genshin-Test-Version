# -*- coding: utf-8 -*-
"""核实：bookmark 当前内容/时间 vs 最近一次游戏运行时间"""
import os, io, re, sys, datetime, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
o = []

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'common', 'bookmarks', '3_The_Traveler.txt')
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    seq = re.findall(r'(?m)^[ \t]*"([A-Z]{3})"\s*=\s*\{', t)
    o.append(f'{label} bookmark: mtime={mt:%m-%d %H:%M:%S}, {len(t)}B')
    o.append(f'  tag 序列: {seq}')
    # 前 8 个（主要国家）
    o.append(f'  前 8 = {seq[:8]}')

o.append('')
for f in ('error.log', 'game.log'):
    fp = os.path.join(LOGS, f)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    o.append(f'{f}: mtime={mt:%m-%d %H:%M:%S}')
o.append('')
o.append(f'现在时间: {datetime.datetime.now():%m-%d %H:%M:%S}')
import subprocess
r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
o.append(f'hoi4 进程数: {r.stdout.strip()}')
print('\n'.join(o))

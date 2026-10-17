# -*- coding: utf-8 -*-
"""frontendmainview.gui 缺元素补齐 + 跑游戏复验 UI 报错"""
import os, io, re, sys, shutil, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
o = []

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig')

def names(t):
    return set(re.findall(r'name\s*=\s*"([^"]+)"', t))

g = rd(os.path.join(G, 'interface', 'frontendmainview.gui'))
v = rd(os.path.join(V, 'interface', 'frontendmainview.gui'))
mg, mv = names(g), names(v)
o.append(f'mod {len(mg)} / 原版 {len(mv)} 元素')
o.append(f'原版有 mod 无（{len(mv - mg)}）: {sorted(mv - mg)}')
o.append(f'mod 独有（{len(mg - mv)}）: {sorted(mg - mv)}')

# 日志里 frontendmainview 相关报错
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
o.append('')
o.append('===== 日志中所有 "Could not find ... in window" =====')
import collections
c = collections.Counter()
for m in re.finditer(r'Could not find "([^"]+)" in window (\S+)', t):
    c[(m.group(2), m.group(1))] += 1
for (w, e), n in c.most_common(30):
    o.append(f'  ×{n}: {e}  @ {w}')
io.open(os.path.join(REPO, 'tools', 'fm_recon_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

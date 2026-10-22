# -*- coding: utf-8 -*-
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
o = []

t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
o.append('===== 当前 error.log 的 sprite/window 报错 =====')
for l in t.splitlines():
    if 'Could not find sprite type' in l or 'Could not find "' in l:
        o.append('  ' + l.strip()[:180])

# first_row 四个按钮的 sprite 是否存在
sn = set()
for fp in glob.glob(os.path.join(G, 'interface', '**', '*.gfx'), recursive=True):
    tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    sn |= set(re.findall(r'name\s*=\s*"([^"]+)"', tt))
o.append('')
o.append('===== first_row 按钮 sprite 存在性 =====')
for s in ('homepage', 'forum', 'discord', 'privacy', 'bluesky', 'twitter', 'x', 'youtube', 'facebook', 'instagram'):
    o.append(f'  {s}: {"有" if s in sn else "【缺】"}')
io.open(os.path.join(G, '..', 'tools', 'soc2_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

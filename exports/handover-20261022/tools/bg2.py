# -*- coding: utf-8 -*-
import os, io, re, sys, glob, datetime
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
o = []

# 1) 最新日志中的 sprite/window 报错
ep = os.path.join(LOGS, 'error.log')
mt = datetime.datetime.fromtimestamp(os.path.getmtime(ep))
t = io.open(ep, 'rb').read().decode('utf-8-sig', errors='replace')
lines = t.splitlines()
o.append(f'===== error.log mtime={mt:%m-%d %H:%M}, {len(lines)} 行 =====')
seen = set()
for l in lines:
    if 'Could not find sprite type' in l or 'Could not find "' in l or 'texture' in l.lower() and 'frontend' in l.lower():
        key = l.strip()
        if key not in seen:
            seen.add(key)
            o.append('  ' + key[:180])

# 2) gui 的 background 区段（L55-L165）
t2 = io.open(os.path.join(G, 'interface', 'frontendmainview.gui'), 'rb').read().decode('utf-8-sig', errors='replace')
o.append('')
o.append('===== mod frontendmainview.gui L55-L170 =====')
for i, l in enumerate(t2.splitlines(), 1):
    if 55 <= i <= 170:
        o.append(f'  L{i}: {l.strip()[:150]}')

# 3) loadingscreens 目录
o.append('')
for label, root in [('mod', G), ('原版', V)]:
    d = os.path.join(root, 'gfx', 'loadingscreens')
    if os.path.isdir(d):
        fs = sorted(os.listdir(d))
        o.append(f'  [{label}] loadingscreens: {len(fs)} 个: {fs[:10]}')
    else:
        o.append(f'  [{label}] 无 loadingscreens')
    # 相关 gfx 定义文件
    for fp in glob.glob(os.path.join(root, 'interface', '*.gfx')):
        tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        if 'loadingscreen' in tt.lower():
            names = sorted(set(re.findall(r'name\s*=\s*"(GFX_loadingscreen[^"]*)"', tt, re.I)))
            o.append(f'    {os.path.basename(fp)}: {len(names)} 个 loadingscreen sprite: {names[:8]}')
print('\n'.join(o))
io.open(os.path.join(G, '..', 'tools', 'bg2_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))

# -*- coding: utf-8 -*-
"""按判官日志修 buildings.txt（149 行 col1 + 74 行改名）+ 港口复验 + 跑游戏复验"""
import os, io, re, sys, shutil, datetime, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'o2_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []
for label, root in [('repo', G), ('depl', DEPL)]:
    shutil.copy2(os.path.join(root, 'map', 'buildings.txt'), os.path.join(BD, f'{label}_buildings.txt'))
o.append(f'备份: {BD}')

# 解析判官日志（当前 error.log = 用户那次运行）
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
within = {}
for m in re.finditer(r'error at line (\d+): map building\([^)]*\) location is not within specified state\. Supposed to be \'\d+ - [^\']*\' but was \'(\d+) - ', t):
    within[int(m.group(1))] = int(m.group(2))
inv = {}
for m in re.finditer(r'error at line (\d+): map building location has invalid state \((\d+)', t):
    inv[int(m.group(1))] = int(m.group(2))
o.append(f'判官: within {len(within)} 条, invalid {len(inv)} 条')

# 应用：within → was；invalid 701→522, 702→511
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'buildings.txt')
    raw = io.open(fp, 'rb').read()
    lines = raw.split(b'\r\n')
    n1 = n2 = 0
    for ln, val in within.items():
        i = ln - 1
        if 0 <= i < len(lines):
            f = lines[i].decode('utf-8', 'replace').split(';')
            if len(f) == 7:
                f[0] = str(val)
                lines[i] = ';'.join(f).encode('utf-8')
                n1 += 1
    for ln, val in inv.items():
        i = ln - 1
        newv = {701: 522, 702: 511}.get(val)
        if newv and 0 <= i < len(lines):
            f = lines[i].decode('utf-8', 'replace').split(';')
            if len(f) == 7 and int(f[0]) == val:
                f[0] = str(newv)
                lines[i] = ';'.join(f).encode('utf-8')
                n2 += 1
    new = b'\r\n'.join(lines)
    if new.endswith(b'\r\n'):
        new = new[:-2]
    io.open(fp, 'wb').write(new)
    o.append(f'{label}: within 修正 {n1}, 改名修正 {n2}')

# 港口复验：9 个 coastal 省是否有有效 naval_base_spawn 行（col1 = 其州号）
COAST = [56, 467, 1306, 1451, 1960, 3515, 3669, 3673, 3678]
sd = os.path.join(G, 'history', 'states')
p2s = {}
for f in os.listdir(sd):
    if not f.endswith('.txt'):
        continue
    tt = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', tt).group(1))
    for p in re.search(r'provinces\s*=\s*\{([^}]*)\}', tt, re.S).group(1).split():
        p2s[int(p)] = sid
raw = io.open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
blines = [l.decode('utf-8', 'replace') for l in raw.split(b'\r\n')]
o.append('')
o.append('===== 9 个 coastal 省的港口行（修后） =====')
need_add = []
for p in COAST:
    st = p2s.get(p)
    found = []
    for l in blines:
        f = l.split(';')
        if len(f) == 7 and f[1] in ('naval_base_spawn', 'naval_headquarters', 'naval_supply_hub', 'floating_harbor') and f[6] == str(p):
            found.append(l)
    o.append(f'  p{p} (州{st}): col7=={p} 的海军行 {len(found)} 条 {found[:1]}')
    if not p2s.get(p):
        need_add.append(p)
o.append(f'  无所属州的省: {need_add if need_add else "无"}')
a = io.open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'map', 'buildings.txt'), 'rb').read()
o.append(f'双副本一致: {a == b}')
io.open(os.path.join(REPO, 'tools', 'o2_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

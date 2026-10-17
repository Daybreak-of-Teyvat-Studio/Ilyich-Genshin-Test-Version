# -*- coding: utf-8 -*-
"""修 9 个沿海省的港口行 + 补缺失的 naval_base_spawn → 跑游戏复验"""
import os, io, re, sys, shutil, datetime, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'port_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []
for label, root in [('repo', G), ('depl', DEPL)]:
    shutil.copy2(os.path.join(root, 'map', 'buildings.txt'), os.path.join(BD, f'{label}_buildings.txt'))
o.append(f'备份: {BD}')

sd = os.path.join(G, 'history', 'states')
p2s = {}
for f in os.listdir(sd):
    if not f.endswith('.txt'):
        continue
    tt = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', tt).group(1))
    for p in re.search(r'provinces\s*=\s*\{([^}]*)\}', tt, re.S).group(1).split():
        p2s[int(p)] = sid
# positions
pos = {}
tt = io.open(os.path.join(G, 'map', 'positions.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)', tt):
    pos[int(m.group(1))] = (m.group(2), m.group(3), m.group(4))

COAST = [56, 467, 1306, 1451, 1960, 3515, 3669, 3673, 3678]
NAVAL = ('naval_base_spawn', 'naval_headquarters', 'naval_supply_hub', 'coastal_bunker', 'floating_harbor')

for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'buildings.txt')
    raw = io.open(fp, 'rb').read()
    lines = [l.decode('utf-8') for l in raw.split(b'\r\n')]
    n_fix = 0
    for i, l in enumerate(lines):
        f = l.split(';')
        if len(f) != 7:
            continue
        if f[1] in NAVAL and f[6].isdigit() and int(f[6]) in COAST:
            p = int(f[6])
            want = p2s.get(p)
            if want and int(f[0]) != want:
                f[0] = str(want)
                lines[i] = ';'.join(f)
                n_fix += 1
    # 补 naval_base_spawn（若该省没有 col7==它 的 naval_base_spawn 行）
    add = 0
    for p in COAST:
        has = any(l.split(';')[1] == 'naval_base_spawn' and l.split(';')[6] == str(p) for l in lines if len(l.split(';')) == 7)
        if not has:
            st = p2s.get(p)
            x, y, z = pos.get(p, ('0', '9.50', '0'))
            lines.append(f'{st};naval_base_spawn;{float(x):.2f};9.50;{float(z):.2f};0.00;{p}')
            add += 1
            o.append(f'  {label} 补港口行 p{p} 州{st}')
    out = '\r\n'.join(lines).rstrip('\r\n')
    io.open(fp, 'wb').write(out.encode('utf-8'))
    o.append(f'{label}: 修海军行 col1 {n_fix}, 补港口行 {add}')

# 跑游戏复验
o.append('')
o.append('===== 跑游戏复验 =====')
subprocess.run(['powershell', '-NoProfile', '-Command',
                "$p = Start-Process -FilePath 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV\\hoi4.exe' "
                "-ArgumentList '-debug' -WorkingDirectory 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV' -PassThru; "
                "Start-Sleep -Seconds 95; if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }"])
time.sleep(3)
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
lines2 = t.splitlines()
for k in ('MAP_ERROR', 'not within specified state', 'invalid state', 'invalid arguments',
          'coastal but has no port', 'no provinces in state', 'fractioned'):
    o.append(f'  [{len([1 for l in lines2 if k in l])}] {k}')
o.append('  末 6 行:')
for l in lines2[-6:]:
    o.append('    ' + l[:170])
a = io.open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'map', 'buildings.txt'), 'rb').read()
o.append(f'buildings 双副本一致: {a == b}, {len(a)}B, {len(a.split(chr(13).encode() + chr(10).encode()))} 行')
io.open(os.path.join(REPO, 'tools', 'port_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

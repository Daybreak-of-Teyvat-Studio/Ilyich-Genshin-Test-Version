# -*- coding: utf-8 -*-
import os, io, re, sys, shutil, datetime, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'final_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []
o.append(f'备份: {BD}')

# 0) 看 14_sea_on_actions.txt 的 6 行
F = 'common/on_actions/14_sea_on_actions.txt'
for label, root in [('仓库', G)]:
    fp = os.path.join(root, F.replace('/', os.sep))
    shutil.copy2(fp, os.path.join(BD, 'repo_14_sea_on_actions.txt'))
    t = io.open(fp, 'rb').read().decode('utf-8-sig')
    ls = t.splitlines()
    o.append('===== 14_sea_on_actions.txt 命中行 =====')
    for i in (209, 219, 261, 297, 368, 379):
        o.append(f'  L{i}: {ls[i-1].strip()[:150]}')

# 1) 修这些引用（511/522 → 510；701/702 → 522/511；以及任何 >700 的旧号）
MAPALL = {511: 510, 522: 510, 701: 522, 702: 511}
nfix = 0
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, F.replace('/', os.sep))
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    t = raw.decode('utf-8-sig')
    for old, new in MAPALL.items():
        t2, n = re.subn(r'(\bstate\s*=\s*)' + str(old) + r'(?![0-9])', r'\g<1>' + str(new), t)
        if n:
            t = t2
            nfix += n
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t.encode('utf-8'))
o.append(f'  修正引用 {nfix} 处')
# 复查该文件所有 state = N 的 N 是否都存在
t = io.open(os.path.join(G, F.replace('/', os.sep)), 'rb').read().decode('utf-8-sig')
sd = os.path.join(G, 'history', 'states')
ids = set(int(f.split('-')[0]) for f in os.listdir(sd) if f.endswith('.txt'))
bad = sorted(set(int(m.group(1)) for m in re.finditer(r'\bstate\s*=\s*(\d+)', t)) - ids)
o.append(f'  文件内 state= 引用中不存在的州号: {bad if bad else "无 ✓"}')

# 2) 给 474 补生成点（10 条 SL）
SL = [('air_base', 1), ('fuel_silo', 1), ('radar_station', 1), ('nuclear_reactor_spawn', 1),
      ('rocket_site_spawn', 1), ('synthetic_refinery', 1), ('stronghold_network', 1), ('anti_air_building', 3)]
p474 = None
t474 = io.open(os.path.join(sd, '474-State_474.txt'), 'rb').read().decode('utf-8-sig')
p474 = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t474, re.S).group(1).split()]
o.append(f'  474 剩余省份: {p474}')
pos = {}
tt = io.open(os.path.join(G, 'map', 'positions.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)', tt):
    pos[int(m.group(1))] = (m.group(2), m.group(3), m.group(4))
anchor = p474[0] if p474 else None
x, y, z = pos.get(anchor, ('0', '9.5', '0'))
rows = []
for bt, cnt in SL:
    for k in range(cnt):
        rot = 0.00 if k == 0 else round(1.20 * k, 2)
        rows.append(f'474;{bt};{float(x):.2f};9.50;{float(z):.2f};{rot:.2f};0')
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'buildings.txt')
    raw = io.open(fp, 'rb').read()
    shutil.copy2(fp, os.path.join(BD, f'{label}_buildings.txt'))
    lines = [l.decode('utf-8') for l in raw.split(b'\r\n')]
    has = [l for l in lines if len(l.split(';')) == 7 and l.split(';')[0] == '474' and l.split(';')[1] == 'air_base']
    if not has:
        lines += rows
        io.open(fp, 'wb').write('\r\n'.join(lines).rstrip('\r\n').encode('utf-8'))
        o.append(f'  {label}: 为 474 补 {len(rows)} 条生成点（锚省 {anchor} @({x},{z})）')
    else:
        o.append(f'  {label}: 474 已有 air_base {len(has)} 条，跳过')

# 3) 跑游戏复验
o.append('')
o.append('===== 跑游戏复验 =====')
subprocess.run(['powershell', '-NoProfile', '-Command',
                "$p = Start-Process -FilePath 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV\\hoi4.exe' "
                "-ArgumentList '-debug' -WorkingDirectory 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV' -PassThru; "
                "Start-Sleep -Seconds 95; if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }"])
time.sleep(3)
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
l2 = t.splitlines()
for k in ('MAP_ERROR', 'not within specified state', 'invalid state', 'coastal but has no port', 'fractioned', 'no provinces in state'):
    o.append(f'  [{len([1 for l in l2 if k in l])}] {k}')
for l in l2:
    if 'MAP_ERROR' in l:
        o.append('    ' + l.strip()[:170])
for l in l2:
    if 'invalid state' in l:
        o.append('    ' + l.strip()[:170])
io.open(os.path.join(REPO, 'tools', 'final_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

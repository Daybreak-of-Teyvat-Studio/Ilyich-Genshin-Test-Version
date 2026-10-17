# -*- coding: utf-8 -*-
"""修 buildings.txt 三类 nudge 报错：14 行恢复备份值 + 8 行宫殿去 # + 去尾空行"""
import os, io, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK = os.path.join(REPO, '.backups', 'mega014_20261014_220448', '仓库_buildings.txt')
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'bldfix_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []

for label, root in [('repo', G), ('depl', DEPL)]:
    shutil.copy2(os.path.join(root, 'map', 'buildings.txt'), os.path.join(BD, f'{label}_buildings.txt'))
o.append(f'备份: {BD}')

bkl = io.open(BK, 'rb').read().split(b'\r\n')
bkset = {}
for l in bkl:
    f = l.decode('utf-8', 'replace').split(';')
    if len(f) == 7:
        bkset[(f[1], f[2], f[4])] = f[0]

for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'buildings.txt')
    raw = io.open(fp, 'rb').read()
    lines = raw.split(b'\r\n')
    n_fix = n_uncomm = 0
    out = []
    for l in lines:
        s = l.decode('utf-8', 'replace')
        if not s.strip():
            n_fix += 0
            # 去掉纯空行（尾部）
            if l == lines[-1]:
                continue
        # ① 宫殿行去 #
        if s.startswith('#') and ';' in s and s.count(';') == 6:
            body = s.lstrip('#')
            fb = body.split(';')
            if fb[1].endswith('_Palace'):
                out.append(body.encode('utf-8'))
                n_uncomm += 1
                continue
        # ② 14 行恢复备份 col1
        f = s.split(';')
        if len(f) == 7:
            key = (f[1], f[2], f[4])
            if key in bkset and f[0] != bkset[key] and f[1] in ('coastal_bunker', 'naval_supply_hub', 'naval_headquarters'):
                old = f[0]
                f[0] = bkset[key]
                s = ';'.join(f)
                n_fix += 1
                o.append(f'  {label} 海军行 {f[1]}@({f[2]},{f[4]}): {old} → {bkset[key]}')
                out.append(s.encode('utf-8'))
                continue
        out.append(l)
    new = b'\r\n'.join(out)
    if new.endswith(b'\r\n'):
        new = new[:-2]
    io.open(fp, 'wb').write(new)
    chk = io.open(fp, 'rb').read()
    o.append(f'{label}: 修海军行 {n_fix}, 去#宫殿 {n_uncomm}, {len(chk)}B, 尾={chk[-24:]!r}, CRCRLF={chk.count(bytes([13,13,10]))}')

# 双副本一致
a = io.open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'map', 'buildings.txt'), 'rb').read()
o.append(f'双副本一致: {a == b}')
lines = a.split(b'\r\n')
o.append(f'行数 {len(lines)}, 含#行 {sum(1 for l in lines if l.startswith(b"#"))}, 空行 {sum(1 for l in lines if not l.strip())}')
bad7 = [i + 1 for i, l in enumerate(lines) if len(l.decode('utf-8', 'replace').split(';')) != 7]
o.append(f'非7字段行: {bad7 if bad7 else "无 ✓"}')
io.open(os.path.join(REPO, 'tools', 'bldfix_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

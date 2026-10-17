# -*- coding: utf-8 -*-
"""撤销 bldfix 多改的 18 行（恢复重建后的正确值），保留 14 行修正 + 8 行去# + 去尾空行"""
import os, io, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BD = sorted(glob.glob(os.path.join(REPO, '.backups', 'bldfix_*')), key=os.path.getmtime)[-1]
o = [f'参照备份: {BD}']

# 多改的 18 行（type, x, z）→ 应从 bldfix 前备份恢复 col1
WRONG18 = [('coastal_bunker', '2636.38', '886.38'), ('coastal_bunker', '2671.53', '862.00'),
           ('coastal_bunker', '2628.00', '861.82'), ('coastal_bunker', '2654.47', '856.12'),
           ('coastal_bunker', '2269.62', '632.70'),
           ('naval_supply_hub', '2638.00', '884.00'), ('naval_headquarters', '2633.00', '884.00'),
           ('naval_supply_hub', '2671.00', '861.00'), ('naval_headquarters', '2671.00', '860.00'),
           ('naval_supply_hub', '2627.00', '860.00'), ('naval_headquarters', '2626.00', '859.00'),
           ('naval_supply_hub', '2655.00', '854.00'), ('naval_headquarters', '2657.00', '856.00'),
           ('coastal_bunker', '2273.00', '612.00'), ('naval_supply_hub', '2278.00', '610.00'),
           ('naval_supply_hub', '2272.00', '611.00'), ('naval_headquarters', '2272.00', '612.00'),
           ('naval_headquarters', '2277.00', '612.00')]
WSET = set(WRONG18)

# 从 bldfix 前备份取这 18 行的 col1
pre = io.open(os.path.join(BD, 'repo_buildings.txt'), 'rb').read().split(b'\r\n')
preval = {}
for l in pre:
    f = l.decode('utf-8', 'replace').split(';')
    if len(f) == 7 and (f[1], f[2], f[4]) in WSET:
        preval[(f[1], f[2], f[4])] = f[0]
o.append(f'备份中这 18 行的 col1: {preval}')

for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'buildings.txt')
    raw = io.open(fp, 'rb').read()
    lines = raw.split(b'\r\n')
    out = []
    n = 0
    for l in lines:
        s = l.decode('utf-8', 'replace')
        f = s.split(';')
        if len(f) == 7:
            key = (f[1], f[2], f[4])
            if key in WSET and f[0] != preval.get(key):
                f[0] = preval[key]
                s = ';'.join(f)
                n += 1
                o.append(f'  {label} 撤销: {key[0]}@({key[1]},{key[2]}) → {preval[key]}')
        out.append(s.encode('utf-8'))
    new = b'\r\n'.join(out)
    if new.endswith(b'\r\n'):
        new = new[:-2]
    io.open(fp, 'wb').write(new)
    o.append(f'{label}: 撤销 {n} 行, {len(new)}B')
a = io.open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'map', 'buildings.txt'), 'rb').read()
o.append(f'双副本一致: {a == b}')
lines = a.split(b'\r\n')
o.append(f'行数 {len(lines)}, 含#行 {sum(1 for l in lines if l.startswith(b"#"))}, 空行 {sum(1 for l in lines if not l.strip())}')
o.append(f'尾部: {a[-30:]!r}')
io.open(os.path.join(REPO, 'tools', 'undofix_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

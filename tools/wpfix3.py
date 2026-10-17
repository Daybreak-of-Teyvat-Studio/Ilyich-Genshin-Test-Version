# -*- coding: utf-8 -*-
import os, io, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'weatherpositions.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig').rstrip('\r\n')
    lines = t.splitlines()
    has3 = any(l.startswith('3;') for l in lines)
    if not has3:
        lines += ['3;2479.68;9.50;953.76;big', '3;2462.11;9.50;971.91;big']
        io.open(fp, 'wb').write(('\r\n'.join(lines)).encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig')
    print(f'{label} weatherpositions ({len(chk)}字符): {chk.splitlines()}')
print('OK')

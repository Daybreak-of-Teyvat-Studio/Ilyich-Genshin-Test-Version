# -*- coding: utf-8 -*-
"""bookmark tag 去引号（与原生格式一致），双副本（游戏未运行才写）"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
rel = os.path.join('common', 'bookmarks', '3_The_Traveler.txt')
o = []

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
if r.stdout.strip() != '0':
    print('hoi4 运行中，跳过')
    sys.exit(0)

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, rel)
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    t2, n = re.subn(r'(?m)^([ \t]*)"([A-Z]{3})"(\s*=\s*\{)', r'\g<1>\g<2>\g<3>', t)
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    seq = re.findall(r'(?m)^[ \t]*([A-Z]{3})\s*=\s*\{', chk)
    o.append(f'{label}: 去引号 {n} 处; tag 序列={seq[:14]}...; 括号 {chk.count("{")}=={chk.count("}")}')
a = io.open(os.path.join(REPO, rel), 'rb').read()
b = io.open(os.path.join(DEPL, rel), 'rb').read()
o.append(f'双副本一致: {a == b}')
print('\n'.join(o))

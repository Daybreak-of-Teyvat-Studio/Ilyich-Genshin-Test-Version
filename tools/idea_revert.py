# -*- coding: utf-8 -*-
import os, io, sys, shutil, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups\ui_20261017_000603'
rel = os.path.join('interface', 'frontendgamesetupview.gui')
r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
if r.stdout.strip() != '0':
    print('hoi4 运行中，跳过')
    sys.exit(0)
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    src = os.path.join(BK, f'{label}_setup.gui')
    dst = os.path.join(root, rel)
    shutil.copy2(src, dst)
    t = io.open(dst, 'rb').read().decode('utf-8-sig', errors='replace')
    i = t.find('spirit_idea_entry_small')
    print(f'{label}: 已回退 {os.path.getsize(dst)}B | ' + ' '.join(t[i:i+200].split())[:150])
a = io.open(os.path.join(REPO, rel), 'rb').read()
b = io.open(os.path.join(DEPL, rel), 'rb').read()
print('双副本一致:', a == b)

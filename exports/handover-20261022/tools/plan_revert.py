# -*- coding: utf-8 -*-
import os, io, re, sys, shutil, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups\ui_20261017_000603'
o = []

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
if r.stdout.strip() != '0':
    print('hoi4 运行中，跳过')
    sys.exit(0)

# 1) gui 恢复原版（备份）
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    src = os.path.join(BK, f'{label}_setup.gui')
    dst = os.path.join(root, 'interface', 'frontendgamesetupview.gui')
    shutil.copy2(src, dst)
    t = io.open(dst, 'rb').read().decode('utf-8-sig', errors='replace')
    i = t.find('spirit_idea_entry_small')
    o.append(f'{label} gui: 已回退 {os.path.getsize(dst)}B | ' + ' '.join(t[i:i+150].split())[:120])

# 2) bookmark: filters 改回注释
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'common', 'bookmarks', '3_The_Traveler.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    t2, n = re.subn(r'(?m)^\t\tfilters\s*=\s*\{\s*new_content\s+continent\s*\}',
                    '\t\t# filters = { new_content continent }', t)
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    o.append(f'{label} bookmark: filters 改回注释 {n} 处, 现含生效={chr(10)+chr(9)+chr(9)+"filters" in chk}, 括号 {chk.count("{")}=={chk.count("}")}')

for rel in (os.path.join('common', 'bookmarks', '3_The_Traveler.txt'), os.path.join('interface', 'frontendgamesetupview.gui')):
    a = io.open(os.path.join(REPO, rel), 'rb').read()
    b = io.open(os.path.join(DEPL, rel), 'rb').read()
    o.append(f'{rel}: 双副本一致={a == b}')
print('\n'.join(o))

# -*- coding: utf-8 -*-
"""bug1 第二步：mainmenu_dlc_ownership 窗口高度 583 → 684（与原版一致），双副本"""
import os, io, re, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
rel = os.path.join('interface', 'frontendmainview.gui')
o = []

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig', errors='replace')

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, rel)
    t = rd(fp)
    m = re.search(r'(name\s*=\s*"mainmenu_dlc_ownership"[\s\S]*?size\s*=\s*\{\s*width\s*=\s*370\s*height\s*=\s*)(\d+)', t)
    if not m:
        o.append(f'{label}: 未找到 mainmenu_dlc_ownership 尺寸 ✗')
        continue
    old = m.group(2)
    t2 = t[:m.start(2)] + '684' + t[m.end(2):]
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    m2 = re.search(r'name\s*=\s*"mainmenu_dlc_ownership"[\s\S]*?size\s*=\s*\{\s*width\s*=\s*370\s*height\s*=\s*(\d+)', chk)
    o.append(f'{label}: height {old} → {m2.group(1) if m2 else "?"}, 括号 {chk.count("{")}=={chk.count("}")}')

a = io.open(os.path.join(REPO, rel), 'rb').read()
b = io.open(os.path.join(DEPL, rel), 'rb').read()
o.append(f'双副本一致: {a == b} ({len(a)}B)')
open(os.path.join(REPO, '..', 'tools', 'dlc_h_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

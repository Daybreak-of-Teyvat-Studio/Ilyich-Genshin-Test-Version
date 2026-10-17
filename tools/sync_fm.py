# -*- coding: utf-8 -*-
import os, io, sys, shutil, hashlib, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
rel = os.path.join('interface', 'frontendmainview.gfx')

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
running = r.stdout.strip() != '0'
print('hoi4 运行中:', running)
if running:
    print('游戏仍在运行，不同步（等退出后再来）')
    sys.exit(0)

src = os.path.join(REPO, rel)
dst = os.path.join(DEPL, rel)
shutil.copy2(src, dst)
a = io.open(src, 'rb').read()
b = io.open(dst, 'rb').read()
print(f'已同步 frontendmainview.gfx: {len(b)}B, 字节一致={a == b}, SHA256 一致={hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()}')
t = b.decode('utf-8-sig')
for n in ('GFX_frontend_banner_dlc051', 'GFX_frontend_medal_dlc051', 'GFX_frontend_banner_dlc052', 'GFX_frontend_medal_dlc052'):
    print(f'  {n}: {"✓" if n in t else "✗"}')

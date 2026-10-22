# -*- coding: utf-8 -*-
import os, io, re, sys, difflib, shutil, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
o = []

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig', errors='replace')

bt = rd(os.path.join(B, 'interface', 'frontendmainview.gui'))
gt = rd(os.path.join(G, 'interface', 'frontendmainview.gui'))
o.append(f'Beta={len(bt)}B, Gamma当前={len(gt)}B')
o.append(f'Beta 含 mainmenu_dlc_ownership={"mainmenu_dlc_ownership" in bt}, bluesky_button={"bluesky_button" in bt}, 双空格风格={"name  =" in bt}')
o.append(f'Gamma当前含 bluesky_button={"bluesky_button" in gt}')
# Beta 与 Gamma 原始（去掉我插入的 7 块后）应一致：对比 Beta vs Gamma当前 的差集
mb = set(re.findall(r'name\s*=\s*"([^"]+)"', bt))
mg = set(re.findall(r'name\s*=\s*"([^"]+)"', gt))
o.append(f'Beta 有 Gamma当前无: {sorted(mb - mg)}')
o.append(f'Gamma当前多出(Beta无): {sorted(mg - mb)}  ← 应为我插入的 7 个')

# 用 Beta 覆盖（双副本）
for label, root in [('仓库', G), ('副本', DEPL)]:
    dst = os.path.join(root, 'interface', 'frontendmainview.gui')
    shutil.copy2(dst, os.path.join(REPO, '.backups', f'prebeta_{label}_fm.gui'))
    io.open(dst, 'wb').write(bt.encode('utf-8'))
    chk = rd(dst)
    o.append(f'  {label} 已用 Beta 版覆盖: {len(chk)}B, 括号 {chk.count("{")}=={chk.count("}")}, 含 second_row={"second_row" in chk}')
a = io.open(os.path.join(G, 'interface', 'frontendmainview.gui'), 'rb').read()
b = io.open(os.path.join(DEPL, 'interface', 'frontendmainview.gui'), 'rb').read()
o.append(f'双副本一致: {a == b}')

o.append('')
o.append('===== 跑游戏复验 =====')
subprocess.run(['powershell', '-NoProfile', '-Command',
                "$p = Start-Process -FilePath 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV\\hoi4.exe' "
                "-ArgumentList '-debug' -WorkingDirectory 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV' -PassThru; "
                "Start-Sleep -Seconds 95; if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }"])
time.sleep(3)
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
l2 = t.splitlines()
for k in ('Could not find sprite type', 'Could not find "', 'MAP_ERROR', 'not within specified state'):
    o.append(f'  [{len([1 for l in l2 if k in l])}] {k}')
for l in l2:
    if 'Could not find sprite type' in l or 'Could not find "' in l:
        o.append('    ' + l.strip()[:180])
io.open(os.path.join(REPO, 'tools', 'ui_beta_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

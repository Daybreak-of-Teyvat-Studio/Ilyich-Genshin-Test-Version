# -*- coding: utf-8 -*-
"""收尾：回退 frontendmainview.gui；补 GFX_country_filter_entry；跑游戏复验"""
import os, io, re, sys, shutil, glob, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
o = []

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig')

def close_brace(t, start):
    depth = 0
    k = start
    while k < len(t):
        if t[k] == '{':
            depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    return -1

def find_block(t, name):
    m = re.search(r'name\s*=\s*"' + re.escape(name) + r'"', t)
    if not m:
        return None
    start = None
    for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
        start = m2
    if start is None:
        return None
    bs = t.index('{', start.start())
    be = close_brace(t, bs)
    return t[start.start():be]

# 1) 回退 frontendmainview.gui（用 ui_ 备份的原始版）
BKu = sorted(glob.glob(os.path.join(REPO, '.backups', 'ui_*')))[-1]
src = os.path.join(BKu, '仓库_fm.gui')
o.append(f'回退源: {src} (存在={os.path.exists(src)})')
for label, root in [('仓库', G), ('副本', DEPL)]:
    dst = os.path.join(root, 'interface', 'frontendmainview.gui')
    shutil.copy2(src, dst)
    chk = rd(dst)
    o.append(f'  {label} frontendmainview.gui 回退: {len(chk)}B, 括号 {chk.count("{")}=={chk.count("}")}')

# 2) 补 GFX_country_filter_entry 到 mod 的 frontendgamesetupview.gfx
tv = rd(os.path.join(V, 'interface', 'frontendgamesetupview.gfx'))
blk = find_block(tv, 'GFX_country_filter_entry')
o.append(f'GFX_country_filter_entry 块提取: {"成功" if blk else "失败"}')
if blk:
    for label, root in [('仓库', G), ('副本', DEPL)]:
        fp = os.path.join(root, 'interface', 'frontendgamesetupview.gfx')
        t = rd(fp)
        shutil.copy2(fp, os.path.join(BKu, f'{label}_setup.gfx'))
        if 'GFX_country_filter_entry' in t:
            o.append(f'  {label} 已存在，跳过')
            continue
        i = t.find('spriteTypes')
        bs = t.index('{', i)
        be = close_brace(t, bs)
        ins = t.rfind('\n', 0, be - 1) + 1
        t2 = t[:ins] + blk + '\n' + t[ins:]
        io.open(fp, 'wb').write(t2.encode('utf-8'))
        chk = rd(fp)
        o.append(f'  {label} setup.gfx 加 sprite: 含={{"GFX_country_filter_entry" in chk}}, 括号 {chk.count("{")}=={chk.count("}")}')

# 3) 检查社媒 sprite 是否齐全（core.gfx 是否含 facebook/instagram）
cg = rd(os.path.join(G, 'interface', 'core.gfx'))
o.append('')
o.append('===== core.gfx 社媒 sprite 检查 =====')
for s in ('bluesky', 'x', 'twitter', 'youtube', 'discord', 'facebook', 'instagram'):
    cnt = len(re.findall(r'name\s*=\s*"' + re.escape(s) + r'"', cg))
    o.append(f'  {s}: {cnt} 处' + ('  ⚠ 缺' if cnt == 0 else ''))

# 4) 双副本一致
for rel in ('interface/core.gfx', 'interface/frontendmainview.gfx', 'interface/frontendmainview.gui',
            'interface/frontendgamesetupview.gui', 'interface/frontendgamesetupview.gfx'):
    a = io.open(os.path.join(G, rel.replace('/', os.sep)), 'rb').read()
    b = io.open(os.path.join(DEPL, rel.replace('/', os.sep)), 'rb').read()
    o.append(f'{rel}: 双副本一致={a == b}')

# 5) 跑游戏复验
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
io.open(os.path.join(REPO, 'tools', 'ui_final_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

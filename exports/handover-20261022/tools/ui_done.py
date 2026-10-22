# -*- coding: utf-8 -*-
import os, io, re, sys, shutil, subprocess, time
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
    depth = 0; k = start
    while k < len(t):
        if t[k] == '{': depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0: return k + 1
        k += 1
    return -1

def find_block(t, name):
    m = re.search(r'name\s*=\s*"' + re.escape(name) + r'"', t)
    if not m: return None
    start = None
    for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
        start = m2
    if start is None: return None
    bs = t.index('{', start.start())
    be = close_brace(t, bs)
    return t[start.start():be]

blk = find_block(rd(os.path.join(V, 'interface', 'frontendgamesetupview.gfx')), 'GFX_country_filter_entry')
o.append(f'提取 GFX_country_filter_entry: {"成功" if blk else "失败"}')
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'frontendgamesetupview.gfx')
    t = rd(fp)
    if 'GFX_country_filter_entry' in t:
        o.append(f'  {label} 已存在 ✓')
        continue
    i = t.find('spriteTypes'); bs = t.index('{', i); be = close_brace(t, bs)
    ins = t.rfind('\n', 0, be - 1) + 1
    io.open(fp, 'wb').write((t[:ins] + blk + '\n' + t[ins:]).encode('utf-8'))
    chk = rd(fp)
    o.append(f'  {label} 已加 sprite: 含={"GFX_country_filter_entry" in chk}, 括号 {chk.count("{")}=={chk.count("}")}')
a = io.open(os.path.join(G, 'interface', 'frontendgamesetupview.gfx'), 'rb').read()
b = io.open(os.path.join(DEPL, 'interface', 'frontendgamesetupview.gfx'), 'rb').read()
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
for k in ('Could not find sprite type', 'Could not find "', 'MAP_ERROR', 'not within specified state',
          'coastal but has no port', 'fractioned'):
    o.append(f'  [{len([1 for l in l2 if k in l])}] {k}')
for l in l2:
    if 'Could not find sprite type' in l or 'Could not find "' in l:
        o.append('    ' + l.strip()[:180])
io.open(os.path.join(REPO, 'tools', 'ui_done_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

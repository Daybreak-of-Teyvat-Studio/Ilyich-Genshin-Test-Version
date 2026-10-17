# -*- coding: utf-8 -*-
"""dlc_button 结构对比（mod vs 原版）+ 窗口几何差异定位"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\dlcbtn_out.txt'
o = []

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig', errors='replace')

def close_brace(t, start):
    depth = 0; k = start
    while k < len(t):
        if t[k] == '{': depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0: return k + 1
        k += 1
    return -1

def blocks_named(t, name):
    res = []
    for m in re.finditer(r'name\s*=\s*"' + re.escape(name) + r'"', t):
        start = None
        for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
            start = m2
        if start is None:
            continue
        bs = t.index('{', start.start())
        be = close_brace(t, bs)
        res.append(t[start.start():be])
    return res

for label, root in [('mod', G), ('原版', V)]:
    t = rd(os.path.join(root, 'interface', 'frontendmainview.gui'))
    for i, b in enumerate(blocks_named(t, 'dlc_button')):
        o.append(f'########## {label} dlc_button #{i+1} ##########')
        for l in b.splitlines():
            o.append('  ' + l.strip()[:150])
        o.append('')

# 窗口高度对比
for label, root in [('mod', G), ('原版', V)]:
    t = rd(os.path.join(root, 'interface', 'frontendmainview.gui'))
    m = re.search(r'name\s*=\s*"mainmenu_dlc_ownership".*?size\s*=\s*\{\s*width\s*=\s*(\d+)\s*height\s*=\s*(\d+)', t, re.S)
    o.append(f'{label} mainmenu_dlc_ownership 尺寸: {m.groups() if m else "?"}')

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
o.append(f'hoi4 运行中: {r.stdout.strip() != "0"}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

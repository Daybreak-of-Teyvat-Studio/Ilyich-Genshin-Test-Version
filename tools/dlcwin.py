# -*- coding: utf-8 -*-
"""对比 mod/原版 的 mainmenu_dlc_ownership 窗口（DLC 图标列）"""
import os, io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\dlcwin_out.txt'
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

def block(t, name):
    m = re.search(r'name\s*=\s*"' + re.escape(name) + r'"', t)
    if not m: return None
    start = None
    for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
        start = m2
    bs = t.index('{', start.start())
    be = close_brace(t, bs)
    return t[start.start():be]

for label, root in [('mod', G), ('原版', V)]:
    t = rd(os.path.join(root, 'interface', 'frontendmainview.gui'))
    b = block(t, 'mainmenu_dlc_ownership')
    o.append(f'########## {label} mainmenu_dlc_ownership ##########')
    if b:
        for l in b.splitlines():
            o.append('  ' + l.strip()[:150])
    else:
        o.append('  （未找到）')
    o.append('')

# 也找 dlc_button
for label, root in [('mod', G), ('原版', V)]:
    t = rd(os.path.join(root, 'interface', 'frontendmainview.gui'))
    for m in re.finditer(r'(?m)^.*dlc_button.*$', t):
        o.append(f'[{label}] {m.group(0).strip()[:150]}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

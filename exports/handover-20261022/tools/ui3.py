# -*- coding: utf-8 -*-
import os, io, re, sys, difflib, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = os.path.join(REPO, 'tools', 'ui3_out.txt')
o = []

# A) core.gfx 全文 diff（Gamma vs 原版）
a = io.open(os.path.join(G, 'interface', 'core.gfx'), 'rb').read().decode('utf-8-sig').splitlines()
b = io.open(os.path.join(V, 'interface', 'core.gfx'), 'rb').read().decode('utf-8-sig').splitlines()
o.append('===== core.gfx: Gamma vs 原版 diff（前 60 处） =====')
n = 0
for l in difflib.unified_diff(a, b, 'Gamma', '原版', lineterm='', n=1):
    if l.startswith(('+++', '---', '@@')):
        continue
    n += 1
    if n <= 60:
        o.append('  ' + l[:170])
o.append(f'  差异行合计 {n}')

# B) bookmark 3_The_Traveler.txt 全文结构
o.append('')
o.append('===== 3_The_Traveler.txt 结构（Gamma） =====')
tt = io.open(os.path.join(G, 'common', 'bookmarks', '3_The_Traveler.txt'), 'rb').read().decode('utf-8-sig')
o.append(f'  {len(tt)} 字符；前 40 行:')
for l in tt.splitlines()[:40]:
    o.append('    ' + l[:150])
tags = re.findall(r'\b([A-Z]{3})\s*=', tt)
o.append(f'  形如 TAG= 的序列（{len(tags)}）: {tags[:80]}')
tb = io.open(os.path.join(B, 'common', 'bookmarks', '3_The_Traveler.txt'), 'rb').read().decode('utf-8-sig')
o.append(f'  Gamma/Beta 该文件相同: {tt == tb}')

# C) 社媒按钮在 gui 里的引用
o.append('')
o.append('===== frontendmainview.gui 社媒按钮段（Gamma） =====')
tt = io.open(os.path.join(G, 'interface', 'frontendmainview.gui'), 'rb').read().decode('utf-8-sig')
i = tt.find('mainmenu_social_buttons')
o.append('  ' + repr(tt[i - 100:i + 1400]))
vb = os.path.join(V, 'interface', 'frontendmainview.gui')
if os.path.exists(vb):
    tv = io.open(vb, 'rb').read().decode('utf-8-sig')
    j = tv.find('mainmenu_social_buttons')
    o.append('  --- 原版同段 ---')
    o.append('  ' + repr(tv[j - 100:j + 1400]))

# D) DLC 图标/sprite 引用（mod 与原版）
o.append('')
o.append('===== 含 dlc 的 sprite/gui 引用 =====')
for label, root in [('Gamma', G), ('原版', V)]:
    hits = []
    for fp in glob.glob(os.path.join(root, 'interface', '**', '*.gfx'), recursive=True) + \
              glob.glob(os.path.join(root, 'interface', '**', '*.gui'), recursive=True):
        t2 = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        for m in re.finditer(r'(?i)([a-z_0-9]*dlc[a-z_0-9]*)', t2):
            hits.append((os.path.relpath(fp, root), m.group(1)))
    from collections import Counter
    c = Counter(h[1].lower() for h in hits)
    o.append(f'  [{label}] 含 dlc 的标识 {len(c)} 种: {list(c.items())[:25]}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

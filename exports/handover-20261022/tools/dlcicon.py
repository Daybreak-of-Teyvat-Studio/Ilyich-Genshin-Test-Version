# -*- coding: utf-8 -*-
"""找 DLC 图标 sprite 的命名规律：搜原版/ mod 的 interface（dlc052/taog/thunder/pops/potential）"""
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\dlcicon_out.txt'
o = []
PATS = ('dlc052', 'dlc051', 'dlc050', 'taog', 'thunder', 'pops', 'potential_dlc', 'dlc_icon')

def scan(root, label):
    hits = []
    for fp in glob.glob(os.path.join(root, 'interface', '**', '*.gfx'), recursive=True) + \
              glob.glob(os.path.join(root, 'interface', '**', '*.gui'), recursive=True):
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        for i, l in enumerate(t.splitlines(), 1):
            ll = l.lower()
            if any(p in ll for p in PATS):
                hits.append((os.path.relpath(fp, root), i, l.strip()[:150]))
    return hits

for label, root in [('原版', V), ('mod', G)]:
    hits = scan(root, label)
    o.append(f'===== {label}（{len(hits)} 处） =====')
    for h in hits[:50]:
        o.append(f'  [{h[0]}:{h[1]}] {h[2]}')
    o.append('')

# 原版所有含 DLC 字样的贴图文件（gfx/interface 下）
o.append('===== 原版 gfx 下 DLC 相关贴图 =====')
for fp in glob.glob(os.path.join(V, 'gfx', '**', '*'), recursive=True):
    n = os.path.basename(fp).lower()
    if 'dlc' in n and os.path.isfile(fp):
        o.append('  ' + os.path.relpath(fp, V))
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

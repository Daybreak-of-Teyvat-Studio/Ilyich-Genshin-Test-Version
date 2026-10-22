# -*- coding: utf-8 -*-
import os, io, re, sys, difflib, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
BK = None
for d in sorted(glob.glob(os.path.join(REPO, '.backups', 'ui_*'))):
    BK = d
OUT = os.path.join(REPO, 'tools', 'fm2_out.txt')
o = []

def norm(p):
    return io.open(p, 'rb').read().decode('utf-8-sig', errors='replace').replace('\r\n', '\n').split('\n')

# 用未被我改动的备份版（ui_ 备份里的 fm.gui）
bkp = os.path.join(BK, '仓库_fm.gui') if BK else None
a = norm(bkp) if bkp and os.path.exists(bkp) else norm(os.path.join(G, 'interface', 'frontendmainview.gui'))
b = norm(os.path.join(V, 'interface', 'frontendmainview.gui'))
o.append(f'=== frontendmainview.gui: mod(改动前备份) vs 原版 ===')
d = list(difflib.unified_diff(a, b, 'mod', 'vanilla', lineterm='', n=1))
modonly = [l[1:] for l in d if l.startswith('-') and not l.startswith('---')]
vanonly = [l[1:] for l in d if l.startswith('+') and not l.startswith('+++')]
o.append(f'mod 独有行 {len(modonly)}:')
for l in modonly:
    o.append('  ~ ' + l.strip()[:150])
o.append(f'原版独有行 {len(vanonly)}:')
for l in vanonly:
    o.append('  + ' + l.strip()[:150])

# 两个 sprite 定义在哪
o.append('')
o.append('=== 两个缺失 sprite 在 mod/原版 的位置 ===')
for name in ('GFX_subscription_widget_chinese', 'GFX_country_filter_entry'):
    for label, root in [('原版', V), ('Gamma', G)]:
        hits = []
        for fp in glob.glob(os.path.join(root, 'interface', '**', '*.gfx'), recursive=True):
            t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
            if f'"{name}"' in t:
                hits.append(os.path.relpath(fp, root))
        o.append(f'  [{label}] {name}: {hits}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

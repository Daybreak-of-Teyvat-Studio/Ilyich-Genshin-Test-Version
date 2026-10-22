# -*- coding: utf-8 -*-
import os, io, re, sys, glob, difflib
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = os.path.join(REPO, 'tools', 'stale_out.txt')
o = []

def norm(t):
    return [l.rstrip() for l in t.replace('\r\n', '\n').split('\n')]

o.append('===== mod interface/ 中"与原版同名"的文件（潜在旧副本） =====')
rows = []
for fp in glob.glob(os.path.join(G, 'interface', '**', '*'), recursive=True):
    if os.path.isdir(fp):
        continue
    rel = os.path.relpath(fp, G)
    vp = os.path.join(V, rel.replace('/', os.sep))
    if not os.path.exists(vp):
        continue
    a = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    b = io.open(vp, 'rb').read().decode('utf-8-sig', errors='replace')
    na, nb = norm(a), norm(b)
    d = list(difflib.unified_diff(na, nb, lineterm='', n=0))
    add = sum(1 for l in d if l.startswith('+') and not l.startswith('+++'))
    rem = sum(1 for l in d if l.startswith('-') and not l.startswith('---'))
    rows.append((rel, len(a), len(b), add, rem, a == b))
rows.sort(key=lambda r: -(r[3] + r[4]))
o.append(f'  同名文件 {len(rows)} 个（按差异量排序）:')
for rel, la, lb, add, rem, same in rows:
    flag = '  ← 旧副本(原版多内容)' if add > 0 and rem == 0 else ('  ← mod 有改动' if rem > 0 else ('  = 相同' if same else ''))
    o.append(f'  {rel:52s} mod={la:6d} 原版={lb:6d} 原版多={add:4d} mod独有={rem:4d}{flag}')

# core.gfx 全部 mod 独有行（要保留的编辑）
o.append('')
o.append('===== core.gfx: mod 独有行（需在更新后保留） =====')
a = norm(io.open(os.path.join(G, 'interface', 'core.gfx'), 'rb').read().decode('utf-8-sig'))
b = norm(io.open(os.path.join(V, 'interface', 'core.gfx'), 'rb').read().decode('utf-8-sig'))
d = list(difflib.unified_diff(a, b, 'Gamma', '原版', lineterm='', n=1))
for l in d:
    if l.startswith('-') and not l.startswith('---'):
        o.append('  ' + l[:170])

# DLC 横幅/徽章定义在哪个文件
o.append('')
o.append('===== 含 frontend_banner/medal 定义的文件 =====')
for label, root in [('Gamma', G), ('原版', V)]:
    for fp in glob.glob(os.path.join(root, 'interface', '**', '*.gfx'), recursive=True):
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        if 'frontend_banner_dlc' in t or 'frontend_medal_dlc' in t:
            names = sorted(set(re.findall(r'name\s*=\s*"(GFX_frontend_(?:banner|medal)_dlc\w+)"', t)))
            o.append(f'  [{label}] {os.path.relpath(fp, root)}: {len(names)} 个: {names[:26]}')

# frontendgamesetupview.gui 差异摘要
o.append('')
o.append('===== frontendgamesetupview.gui: 原版有 mod 无的元素名 =====')
for name, gpath, vpath in [('frontendgamesetupview.gui', G, V)]:
    a = io.open(os.path.join(gpath, 'interface', name), 'rb').read().decode('utf-8-sig')
    b = io.open(os.path.join(vpath, 'interface', name), 'rb').read().decode('utf-8-sig')
    ga = set(re.findall(r'name\s*=\s*"([^"]+)"', a))
    gb = set(re.findall(r'name\s*=\s*"([^"]+)"', b))
    o.append(f'  mod {len(ga)} 个 / 原版 {len(gb)} 个')
    o.append(f'  原版有 mod 无（{len(gb - ga)}）: {sorted(gb - ga)[:40]}')
    o.append(f'  mod 独有（{len(ga - gb)}）: {sorted(ga - gb)[:20]}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

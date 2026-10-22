# -*- coding: utf-8 -*-
"""bug1 修复：给 mod 的 frontendmainview.gfx 补 4 个 sprites（只改仓库，本地等游戏退出）"""
import os, io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = os.path.join(REPO, 'tools', 'dlc_fix_out.txt')
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

MISS = ['GFX_frontend_banner_dlc051', 'GFX_frontend_medal_dlc051',
        'GFX_frontend_banner_dlc052', 'GFX_frontend_medal_dlc052']
tv = rd(os.path.join(V, 'interface', 'frontendmainview.gfx'))
blocks = []
for n in MISS:
    b = find_block(tv, n)
    if b:
        blocks.append(b)
        tx = re.search(r'texturefile\s*=\s*"([^"]+)"', b)
        tex = tx.group(1) if tx else '?'
        exists_mod = os.path.exists(os.path.join(G, tex.replace('//', '/').lstrip('/')))
        exists_van = os.path.exists(os.path.join(V, tex.replace('//', '/').lstrip('/')))
        o.append(f'  {n}: 贴图={tex} 原版有={exists_van} mod有={exists_mod}')
    else:
        o.append(f'  ⚠ 原版找不到 {n}')
o.append(f'提取 {len(blocks)}/4 块')

fp = os.path.join(G, 'interface', 'frontendmainview.gfx')
t = rd(fp)
if 'GFX_frontend_medal_dlc052' in t:
    o.append('仓库已含 medal_dlc052，无需重复 ✓')
else:
    i = t.find('spriteTypes')
    bs = t.index('{', i)
    be = close_brace(t, bs)
    ins = t.rfind('\n', 0, be - 1) + 1
    t2 = t[:ins] + '\n'.join(blocks) + '\n' + t[ins:]
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    o.append(f'仓库已写入: {len(t2)}B, 括号 {chk.count("{")}=={chk.count("}")}')
    for n in MISS:
        o.append(f'  {n}: {"✓" if n in chk else "✗"}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

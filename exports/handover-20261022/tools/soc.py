# -*- coding: utf-8 -*-
"""bug3 侦察：主菜单社媒行（social buttons）完整块 + 每个按钮引用的 sprite 是否存在"""
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\soc_out.txt'
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
    if start is None: return None
    bs = t.index('{', start.start())
    be = close_brace(t, bs)
    return t[start.start():be]

for label, root in [('mod', G), ('原版', V)]:
    t = rd(os.path.join(root, 'interface', 'frontendmainview.gui'))
    b = block(t, 'mainmenu_social_buttons')
    o.append(f'########## {label} mainmenu_social_buttons ##########')
    if b:
        for l in b.splitlines():
            o.append('  ' + l.strip()[:150])
        # 该块引用的 sprite
        refs = sorted(set(re.findall(r'(?:quadTextureSprite|spriteType|buttonFont)\s*=\s*"([^"]+)"', b)))
        o.append(f'  --> sprite 引用: {refs}')
    o.append('')

# mod 的 gui 里所有含 x/twitter/bluesky 的行
o.append('===== mod gui 中 x/twitter/bluesky 引用 =====')
for fp in glob.glob(os.path.join(G, 'interface', '**', '*.gui'), recursive=True):
    t = rd(fp)
    for i, l in enumerate(t.splitlines(), 1):
        if re.search(r'(?i)(twitter|bluesky|"(x)"|social)', l):
            o.append(f'  [{os.path.relpath(fp, G)}:{i}] {l.strip()[:140]}')

# mod 的 gfx 里 sprite 名集合（判断 'x' 是否存在）
snames = set()
for fp in glob.glob(os.path.join(G, 'interface', '**', '*.gfx'), recursive=True):
    t = rd(fp)
    snames |= set(re.findall(r'name\s*=\s*"([^"]+)"', t))
o.append('')
o.append(f"mod sprite 总数 {len(snames)}; 含 'x'={'x' in snames}, 'twitter'={'twitter' in snames}, 'bluesky'={'bluesky' in snames}")
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

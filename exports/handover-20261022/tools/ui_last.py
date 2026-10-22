# -*- coding: utf-8 -*-
import os, io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
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
    o.append(f'  {label} 已加: 含={"GFX_country_filter_entry" in chk}, 括号 {chk.count("{")}=={chk.count("}")}')

# 终态清点
o.append('')
for rel, keys in [('interface/core.gfx', ['"x"', '"bluesky"', 'GFX_button_238x38']),
                  ('interface/frontendmainview.gfx', ['GFX_frontend_banner_dlc051', 'GFX_frontend_banner_dlc052', 'GFX_frontend_medal_dlc051']),
                  ('interface/frontendmainview.gui', ['bluesky_button', 'second_row', 'discord_button']),
                  ('interface/frontendgamesetupview.gui', ['"filters"', '"more_countries"', '"new_content"', '"country_name"', 'GFX_country_filter_entry']),
                  ('interface/frontendgamesetupview.gfx', ['GFX_country_filter_entry'])]:
    t = rd(os.path.join(G, rel.replace('/', os.sep)))
    res = {k: (k in t) for k in keys}
    o.append(f'{rel}: {res}, 括号 {t.count("{")}=={t.count("}")}')
a = io.open(os.path.join(G, 'interface', 'frontendgamesetupview.gfx'), 'rb').read()
b = io.open(os.path.join(DEPL, 'interface', 'frontendgamesetupview.gfx'), 'rb').read()
o.append(f'setup.gfx 双副本一致: {a == b}')
io.open(os.path.join(REPO, 'tools', 'ui_last_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

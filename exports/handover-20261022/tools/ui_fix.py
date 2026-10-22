# -*- coding: utf-8 -*-
"""UI 修复：core.gfx/frontendmainview.gfx 补 sprite；两个 .gui 补元素 + 修笔误"""
import os, io, re, sys, shutil, datetime, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'ui_{stamp}')
os.makedirs(BD, exist_ok=True)
o = [f'备份: {BD}']

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig')

def close_brace(t, start):
    """从 start（'{' 的位置）返回配对 '}' 的下标+1"""
    depth = 0
    k = start
    while k < len(t):
        if t[k] == '{':
            depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    return -1

def find_block_by_name(t, name, back_kw=None):
    """返回定义 name = "<name>" 的块的文本（含起始关键字）"""
    pat = re.compile(r'name\s*=\s*"' + re.escape(name) + r'"')
    m = pat.search(t)
    if not m:
        return None
    # 向前找块起始关键字
    ls = t.rfind('\n', 0, m.start()) + 1
    start = None
    for m2 in re.finditer(r'(?m)^([ \t]*)([A-Za-z_]+)\s*=\s*\{', t[:m.start()]):
        last = m2
        start = m2
    if start is None:
        return None
    bstart = t.index('{', start.start())
    bend = close_brace(t, bstart)
    return t[start.start():bend], start.start(), bend

def insert_into_parent(t, parent_name, block_text):
    """把 block_text 插到 name=<parent_name> 的块的收尾 } 之前"""
    pat = re.compile(r'name\s*=\s*"' + re.escape(parent_name) + r'"')
    m = pat.search(t)
    if not m:
        return t, False
    # 找该父块的起始
    start = None
    for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
        start = m2
    if start is None:
        return t, False
    bstart = t.index('{', start.start())
    bend = close_brace(t, bstart)
    # 在收尾 } 之前的行首插入
    ins = t.rfind('\n', 0, bend - 1) + 1
    return t[:ins] + block_text.rstrip() + '\n' + t[ins:], True

# ---- 1) core.gfx：补 8 个 sprite ----
MISS_GFX = ['x', 'GFX_button_123x34_gray', 'GFX_button_238x38', 'GFX_edit_designer_notes_button',
            'GFX_generic_circle_background', 'GFX_leader_rescue_raid_button',
            'GFX_red_cross_texticon', 'GFX_warning_11x24']
tv = rd(os.path.join(V, 'interface', 'core.gfx'))
blocks = []
for n in MISS_GFX:
    r = find_block_by_name(tv, n)
    if r:
        blocks.append(r[0])
    else:
        o.append(f'  ⚠ 原版 core.gfx 未找到 sprite {n}')
o.append(f'core.gfx 待插入 sprite: {len(blocks)}')
add = '\n'.join(blocks)
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'core.gfx')
    t = rd(fp)
    shutil.copy2(fp, os.path.join(BD, f'{label}_core.gfx'))
    # 插在 spriteTypes 块收尾前
    i = t.find('spriteTypes')
    bstart = t.index('{', i)
    bend = close_brace(t, bstart)
    ins = t.rfind('\n', 0, bend - 1) + 1
    t2 = t[:ins] + add + '\n' + t[ins:]
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    o.append(f'  {label} core.gfx: {len(t2)}B, x sprite={"name = \"x\"" in chk}, 括号 {chk.count("{")}=={chk.count("}")}')

# ---- 2) frontendmainview.gfx：补 3 个 DLC sprite ----
MISS_DLC = ['GFX_frontend_banner_dlc051', 'GFX_frontend_banner_dlc052', 'GFX_frontend_medal_dlc051']
tv2 = rd(os.path.join(V, 'interface', 'frontendmainview.gfx'))
bl2 = []
for n in MISS_DLC:
    r = find_block_by_name(tv2, n)
    if r:
        bl2.append(r[0])
    else:
        o.append(f'  ⚠ 原版 frontendmainview.gfx 未找到 {n}')
o.append(f'frontendmainview.gfx 待插入: {len(bl2)}')
add2 = '\n'.join(bl2)
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'frontendmainview.gfx')
    t = rd(fp)
    shutil.copy2(fp, os.path.join(BD, f'{label}_fm.gfx'))
    i = t.find('spriteTypes')
    bstart = t.index('{', i)
    bend = close_brace(t, bstart)
    ins = t.rfind('\n', 0, bend - 1) + 1
    t2 = t[:ins] + add2 + '\n' + t[ins:]
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    o.append(f'  {label} fm.gfx: dlc052={"GFX_frontend_banner_dlc052" in chk}, 括号 {chk.count("{")}=={chk.count("}")}')

# ---- 3) frontendgamesetupview.gui：修笔误 + 补元素 ----
INSERTS = [('gamesetup_interesting_countries_window', 'filters'),
           ('gamesetup_interesting_countries_window', 'more_countries'),
           ('country_entry', 'new_content'),
           ('country_entry', 'country_name'),
           ('country_entry', 'country_leader'),
           ('country_entry_mini', 'new_content')]
tv3 = rd(os.path.join(V, 'interface', 'frontendgamesetupview.gui'))
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'frontendgamesetupview.gui')
    t = rd(fp)
    shutil.copy2(fp, os.path.join(BD, f'{label}_setup.gui'))
    # 笔误
    n_typo = t.count('GFX country filter_entry')
    t = t.replace('GFX country filter_entry', 'GFX_country_filter_entry')
    ok = 0
    for parent, elem in INSERTS:
        r = find_block_by_name(tv3, elem)
        if not r:
            o.append(f'  ⚠ 原版缺元素 {elem}')
            continue
        t2, done = insert_into_parent(t, parent, r[0])
        if done:
            t = t2
            ok += 1
        else:
            o.append(f'  ⚠ 父窗口 {parent} 未找到（元素 {elem}）')
    io.open(fp, 'wb').write(t.encode('utf-8'))
    chk = rd(fp)
    o.append(f'  {label} setup.gui: 修笔误 {n_typo}, 插入元素 {ok}/{len(INSERTS)}, 括号 {chk.count("{")}=={chk.count("}")}')

# 双副本一致
for rel in ('interface/core.gfx', 'interface/frontendmainview.gfx',
            'interface/frontendmainview.gui', 'interface/frontendgamesetupview.gui'):
    a = io.open(os.path.join(G, rel.replace('/', os.sep)), 'rb').read()
    b = io.open(os.path.join(DEPL, rel.replace('/', os.sep)), 'rb').read()
    o.append(f'{rel}: 双副本一致={a == b}')
io.open(os.path.join(REPO, 'tools', 'ui_fix_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

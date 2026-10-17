# -*- coding: utf-8 -*-
"""回退三个 UI 修复到改前状态"""
import os, io, re, sys, shutil, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
UIBK = os.path.join(REPO, '.backups', 'ui_20261017_000603')
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

# 1) core.gfx / frontendmainview.gfx / frontendgamesetupview.gui ← ui_ 备份
for label, root, pre in [('仓库', G, '仓库'), ('副本', DEPL, '副本')]:
    for src_name, rel in [('core.gfx', 'interface/core.gfx'),
                          ('fm.gfx', 'interface/frontendmainview.gfx'),
                          ('setup.gui', 'interface/frontendgamesetupview.gui')]:
        src = os.path.join(UIBK, f'{pre}_{src_name}')
        dst = os.path.join(root, rel.replace('/', os.sep))
        if os.path.exists(src):
            shutil.copy2(src, dst)
            o.append(f'{label} {rel} 已从备份回退 ({os.path.getsize(dst)}B)')
        else:
            o.append(f'⚠ {label} 缺备份 {src}')

# 2) frontendgamesetupview.gfx：移除我追加的 GFX_country_filter_entry 块（无备份，按块删除）
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'frontendgamesetupview.gfx')
    t = rd(fp)
    m = re.search(r'name\s*=\s*"GFX_country_filter_entry"', t)
    if m:
        # 向前找块起始关键字行首
        start = None
        for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
            start = m2
        bs = t.index('{', start.start())
        be = close_brace(t, bs)
        # 连同其后空行删除
        le = be
        while le < len(t) and t[le] in '\r\n':
            le += 1
        ls = t.rfind('\n', 0, start.start()) + 1
        t = t[:ls] + t[le:]
        io.open(fp, 'wb').write(t.encode('utf-8'))
        o.append(f'{label} frontendgamesetupview.gfx 已移除追加块 ({os.path.getsize(fp)}B)')
    else:
        o.append(f'{label} frontendgamesetupview.gfx 无追加块 ✓')

# 3) frontendmainview.gui 确认 = Beta 原版
bt = rd(os.path.join(B, 'interface', 'frontendmainview.gui'))
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'frontendmainview.gui')
    t = rd(fp)
    same = (t == bt)
    if not same:
        io.open(fp, 'wb').write(bt.encode('utf-8'))
        o.append(f'{label} frontendmainview.gui 用 Beta 版覆盖')
    else:
        o.append(f'{label} frontendmainview.gui 已是原版 ✓ ({len(t)}B)')

# 4) 验证：大小=改前 + 双副本一致 + 括号
o.append('')
for rel, pre_size in [('interface/core.gfx', 39861),
                      ('interface/frontendmainview.gfx', 5348),
                      ('interface/frontendgamesetupview.gui', 53612),
                      ('interface/frontendgamesetupview.gfx', 9046),
                      ('interface/frontendmainview.gui', 16094)]:
    a = io.open(os.path.join(G, rel.replace('/', os.sep)), 'rb').read()
    b = io.open(os.path.join(DEPL, rel.replace('/', os.sep)), 'rb').read()
    ta = a.decode('utf-8-sig', errors='replace')
    o.append(f'{rel}: {len(a)}B (改前字符数≈{pre_size}), 双副本一致={a == b}, 括号 {ta.count("{")}=={ta.count("}")}')
io.open(os.path.join(REPO, 'tools', 'ui_revert_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

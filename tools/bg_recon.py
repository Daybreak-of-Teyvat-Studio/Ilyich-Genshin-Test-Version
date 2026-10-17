# -*- coding: utf-8 -*-
"""侦察：主菜单"更换背景"按钮 + 背景预览图（mod vs 原版 vs Beta）"""
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\bg_recon_out.txt'
o = []

# 1) 本地化里的"更换背景"相关 key
o.append('===== loc 中含"背景"的 key（mod simp_chinese + 原版 english） =====')
for label, root in [('mod', G), ('原版', V)]:
    pats = []
    d = os.path.join(root, 'localisation')
    for fp in glob.glob(os.path.join(d, '**', '*.yml'), recursive=True):
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        for l in t.splitlines():
            if '背景' in l and ('backend' in l.lower() or 'background' in l.lower() or 'BG' in l):
                pats.append((os.path.basename(fp), l.strip()[:130]))
    o.append(f'  [{label}] {pats[:12] if pats else "无"}')

# 2) gui 里含 background/change_bg 的元素
o.append('')
o.append('===== 主菜单 gui 中 background 相关元素（mod vs 原版 vs Beta） =====')
for label, root in [('mod', G), ('Beta', B), ('原版', V)]:
    fp = os.path.join(root, 'interface', 'frontendmainview.gui')
    if not os.path.exists(fp):
        o.append(f'  [{label}] 无')
        continue
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    hits = [(i + 1, l.strip()[:140]) for i, l in enumerate(t.splitlines()) if re.search(r'(?i)background|bg_|change_bg|mainmenu_bg', l)]
    o.append(f'  [{label}] {len(hits)} 处:')
    for i, l in hits[:25]:
        o.append(f'    L{i}: {l}')

# 3) 背景预览图 sprite（frontendmainview.gfx）
o.append('')
o.append('===== frontendmainview.gfx 中 background/bg 相关 sprite =====')
for label, root in [('mod', G), ('原版', V)]:
    fp = os.path.join(root, 'interface', 'frontendmainview.gfx')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    sp = re.findall(r'spriteType\s*=\s*\{([^}]*)\}', t, re.S)
    hits = []
    for b in sp:
        if re.search(r'(?i)background|bg', b):
            nm = re.search(r'name\s*=\s*"([^"]+)"', b)
            tx = re.search(r'texturefile\s*=\s*"([^"]+)"', b)
            hits.append((nm.group(1) if nm else '?', tx.group(1) if tx else '?'))
    o.append(f'  [{label}] {hits[:15]}')

# 4) 背景贴图文件
o.append('')
o.append('===== 背景贴图文件（frontend/bg 目录） =====')
for label, root in [('mod', G), ('原版', V)]:
    fs = []
    for fp in glob.glob(os.path.join(root, 'gfx', '**', '*'), recursive=True):
        low = fp.lower()
        if ('background' in low or 'frontend_bg' in low or 'menu_bg' in low) and os.path.isfile(fp):
            fs.append(os.path.relpath(fp, root))
    o.append(f'  [{label}] {len(fs)} 个: {fs[:12]}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

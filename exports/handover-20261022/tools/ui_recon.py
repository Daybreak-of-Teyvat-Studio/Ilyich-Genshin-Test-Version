# -*- coding: utf-8 -*-
import os, io, re, sys, collections, glob
sys.stdout.reconfigure(encoding='utf-8')
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = os.path.join(REPO, 'tools', 'ui_recon_out.txt')
o = []

t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
# 1) 缺 sprite 类型
sp = collections.Counter()
for m in re.finditer(r'Could not find sprite type \[([^\]]+)\]', t):
    sp[m.group(1)] += 1
o.append(f'===== 缺 sprite 类型 {sum(sp.values())} 条 =====')
for k, v in sp.most_common(40):
    o.append(f'  ×{v}: {k}')
# 2) 缺贴图 / 贴图初始化失败（含社媒/bluesky/dlc 关键词）
o.append('')
o.append('===== 贴图相关报错（按关键词） =====')
for kw in ('social', 'bluesky', 'twitter', 'discord', 'youtube', 'twitch', 'facebook', 'dlc', 'DLC'):
    hits = [l.strip()[:190] for l in t.splitlines() if kw.lower() in l.lower() and ('texture' in l.lower() or 'sprite' in l.lower() or 'could not' in l.lower() or 'couldn' in l.lower())]
    if hits:
        o.append(f'  [{kw}] {len(hits)} 条:')
        for l in hits[:8]:
            o.append('    ' + l)

# 3) mod 的 interface/gfx 里社媒图标定义与贴图文件
o.append('')
o.append('===== 社媒相关（mod 内 spriteTypes / 文件） =====')
for root, label in [(G, 'Gamma'), (B, 'Beta')]:
    pats = []
    for fp in glob.glob(os.path.join(root, 'interface', '**', '*.gfx'), recursive=True) + \
              glob.glob(os.path.join(root, 'gfx', '**', '*.gfx'), recursive=True) + \
              glob.glob(os.path.join(root, 'interface', '**', '*.gui'), recursive=True):
        tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        for m in re.finditer(r'name\s*=\s*"([^"]*(?:social|bluesky|twitter|discord|youtube|twitch|bilibili|weibo)[^"]*)"', tt, re.I):
            pats.append((os.path.relpath(fp, root), m.group(1)))
    if pats:
        o.append(f'  [{label}] sprite 名: {pats[:20]}')
# 社媒贴图文件
o.append('')
o.append('===== 社媒贴图文件（Gamma/Beta/原版） =====')
for root, label in [(G, 'Gamma'), (B, 'Beta'), (V, '原版')]:
    fs = []
    for fp in glob.glob(os.path.join(root, 'gfx', '**', '*'), recursive=True):
        n = os.path.basename(fp).lower()
        if any(k in n for k in ('social', 'bluesky', 'twitter', 'discord', 'youtube', 'twitch')):
            fs.append(os.path.relpath(fp, root))
    o.append(f'  [{label}] {fs[:20] if fs else "无"}')

# 4) DLC 图标：原版 dlc 元数据
o.append('')
o.append('===== 原版 DLC 元数据（dlc/*.txt 与 icon 引用） =====')
dlcdir = os.path.join(V, 'dlc')
if os.path.isdir(dlcdir):
    for f in sorted(os.listdir(dlcdir))[:40]:
        o.append('  ' + f)
o.append('')
o.append('  最新 DLC 相关（按名称含 Postern/Thunder/GoE/BftB 等）:')
for f in glob.glob(os.path.join(dlcdir, '*.txt')) + glob.glob(os.path.join(dlcdir, '*.dlc')):
    tt = io.open(f, 'rb').read().decode('utf-8-sig', errors='replace')
    if any(k in tt for k in ('picture', 'icon')):
        for m in re.finditer(r'(picture|icon)\s*=\s*"?([^"\r\n]+)"?', tt):
            o.append(f'    {os.path.basename(f)}: {m.group(1)} = {m.group(2).strip()}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o[:80]))

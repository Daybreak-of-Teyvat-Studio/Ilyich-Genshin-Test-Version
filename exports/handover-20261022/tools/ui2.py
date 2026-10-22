# -*- coding: utf-8 -*-
import os, io, re, sys, collections, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = os.path.join(REPO, 'tools', 'ui2_out.txt')
o = []

def sprites(fp):
    tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    return tt

# 1) core.gfx 对比
for rel in ('interface/core.gfx',):
    g = os.path.join(G, rel.replace('/', os.sep))
    for label, root in [('原版', V), ('Beta', B)]:
        p = os.path.join(root, rel.replace('/', os.sep))
        o.append(f'{rel}: Gamma={os.path.getsize(g)}B, {label}={os.path.getsize(p) if os.path.exists(p) else "不存在"}B')
    tg = sprites(g)
    tv = sprites(os.path.join(V, rel.replace('/', os.sep)))
    tb = sprites(os.path.join(B, rel.replace('/', os.sep))) if os.path.exists(os.path.join(B, rel.replace('/', os.sep))) else ''
    ng = set(re.findall(r'name\s*=\s*"([^"]+)"', tg))
    nv = set(re.findall(r'name\s*=\s*"([^"]+)"', tv))
    nb = set(re.findall(r'name\s*=\s*"([^"]+)"', tb))
    o.append(f'  sprite 名: Gamma {len(ng)}, 原版 {len(nv)}, Beta {len(nb)}')
    o.append(f'  原版有 Gamma 无（{len(nv - ng)}）: {sorted(nv - ng)[:40]}')
    o.append(f'  Beta 有 Gamma 无（{len(nb - ng)}）: {sorted(nb - ng)[:20]}')
    o.append(f'  Gamma 独有（{len(ng - nv)}）: {sorted(ng - nv)[:20]}')
    # 社媒 sprite 定义原文
    o.append('')
    o.append('  Gamma core.gfx 里 bluesky/twitter/youtube/discord 定义:')
    for m in re.finditer(r'spriteType\s*=\s*\{[^}]*name\s*=\s*"(?:bluesky|twitter|youtube|discord)"[^}]*\}', tg, re.S):
        o.append('    ' + ' '.join(m.group(0).split())[:220])
    o.append('  原版 core.gfx 里同名/相关定义:')
    for m in re.finditer(r'spriteType\s*=\s*\{[^}]*name\s*=\s*"[^"]*(?:bluesky|twitter|youtube|discord)[^"]*"[^}]*\}', tv, re.S):
        o.append('    ' + ' '.join(m.group(0).split())[:220])
    # DLC 图标相关
    o.append('')
    o.append(f'  原版 core.gfx 含 DLC 图标的 sprite 名: {sorted(x for x in nv if "dlc" in x.lower())[:30]}')
    o.append(f'  Gamma core.gfx 含 DLC 图标的 sprite 名: {sorted(x for x in ng if "dlc" in x.lower())[:30]}')

# 2) bookmarks（国家顺序）
o.append('')
o.append('===== bookmarks 对比（国家列表顺序） =====')
for label, root in [('Gamma', G), ('Beta', B), ('原版', V)]:
    d = os.path.join(root, 'common', 'bookmarks')
    if not os.path.isdir(d):
        o.append(f'  [{label}] 无 bookmarks 目录')
        continue
    for f in sorted(os.listdir(d)):
        fp = os.path.join(d, f)
        tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        countries = re.findall(r'(?m)^\s*([A-Z]{3})\s*=\s*\{', tt) or re.findall(r'(?m)^\s*([A-Z]{3})\s*$', tt)
        o.append(f'  [{label}] {f} ({len(tt)}B): 国家数={len(countries)}')
        o.append(f'      顺序: {countries[:60]}')

# 3) 最新 DLC 的图标引用（原版 dlc 元数据）
o.append('')
o.append('===== 原版 dlc/ 全部条目 =====')
dlcdir = os.path.join(V, 'dlc')
ents = sorted(os.listdir(dlcdir))
o.append(f'  {len(ents)} 个: {ents}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

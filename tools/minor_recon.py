# -*- coding: utf-8 -*-
"""小国排序侦察：tag 中文名 / 开局是否有地 / 是否有专属国策树"""
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\minor_recon_out.txt'
o = []

# 1) tag 中文名（country loc: "<TAG>:0" 或 "<TAG>_DEF" 等）
names = {}
for fp in glob.glob(os.path.join(REPO, 'localisation', 'simp_chinese', '*.yml')):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for m in re.finditer(r'(?m)^\s*([A-Z]{3}):\d*\s*"([^"]*)"', t):
        names.setdefault(m.group(1), (m.group(2), os.path.basename(fp)))

# 2) 开局有地（state owner）
owned = {}
sd = os.path.join(REPO, 'history', 'states')
for f in os.listdir(sd):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'owner\s*=\s*(\w+)', t)
    if m:
        owned[m.group(1)] = owned.get(m.group(1), 0) + 1

# 3) 国策树（focus_tree 里 country = { tag = X } 或 list 中出现 X）
trees = {}
for fp in glob.glob(os.path.join(REPO, 'common', 'national_focus', '*.txt')):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for m in re.finditer(r'focus_tree\s*=\s*\{', t):
        bs = m.end() - 1
        depth = 0; k = bs
        while k < len(t):
            if t[k] == '{': depth += 1
            elif t[k] == '}':
                depth -= 1
                if depth == 0: break
            k += 1
        block = t[bs:k + 1]
        cm = re.search(r'country\s*=\s*\{([\s\S]*?)\n\t\}', block)
        if cm:
            for tag in set(re.findall(r'\b([A-Z]{3})\b', cm.group(1))):
                trees.setdefault(tag, []).append(os.path.basename(fp))

CAND = ['RAG', 'ANR', 'DRA', 'GUN', 'FAV', 'LAW', 'KQP', 'GYP', 'SAN', 'VAN', 'PRI', 'ABY', 'SHP', 'CYG', 'BRF']
o.append('===== 候选小国 =====')
for tag in CAND:
    nm = names.get(tag, ('?', ''))[0]
    o.append(f'  {tag}: 名字={nm!r}  开局州数={owned.get(tag, 0)}  国策树={trees.get(tag, [])}')

# 4) 更多：搜 loc 里的 深渊/天理/丘丘 相关 tag
o.append('')
o.append('===== 名字含 深渊/天理/丘丘 的 tag =====')
for tag, (nm, f) in sorted(names.items()):
    if any(k in nm for k in ('深渊', '天理', '丘丘')):
        o.append(f'  {tag}: {nm}  (开局州数={owned.get(tag, 0)}, 树={trees.get(tag, [])}) ({f})')

# 5) 全部有地+有树的小国（参考完整性）
o.append('')
o.append('===== 全部"有地且有专属树"的 tag（排除8大国）=====')
MAJ = {'MOT', 'LYY', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE'}
for tag in sorted(set(owned) & set(trees)):
    if tag in MAJ:
        continue
    o.append(f'  {tag} ({names.get(tag, ("?",))[0]}): 州 {owned[tag]}, 树 {trees[tag]}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

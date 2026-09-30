# -*- coding: utf-8 -*-
"""重写 41 个海州为干净纯海域格式（从现有文件提取 provinces），修海上建筑条目。"""
import os, re, sys, shutil, collections, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
NEW_IDS = list(range(862, 903))
NAME = {862 + i: ('*' if i < 40 else '暗之外海') for i in range(41)}

# 从坏文件提取 provinces
bdir = os.path.join(ROOT, '.backups', 'sea_state_fix_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
newprovs = {}
for sid in NEW_IDS:
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = open(fp, encoding='utf-8-sig', errors='replace').read()
    provs = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
    newprovs[sid] = sorted(provs)
print('provinces 提取完成:', {s: len(v) for s, v in newprovs.items()})

# 重写干净海州
p2s_new = {}
for sid in NEW_IDS:
    ps = newprovs[sid]
    body = (f'state = {{\n'
            f'\tid = {sid}\n'
            f'\tname="STATE_{sid}"\n'
            f'\tmanpower = 0\n'
            f'\tstate_category = ocean\n'
            f'\n'
            f'\thistory = {{\n'
            f'\t}}\n'
            f'\n'
            f'\tprovinces = {{\n'
            f'\t\t{" ".join(map(str, ps))}\n'
            f'\t}}\n'
            f'}}\n')
    with open(os.path.join(ST, f'{sid}-State_{sid}.txt'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(body)
    for p in ps:
        p2s_new[p] = sid
print(f'41 个海州已重写（state_category = ocean，无 owner/建筑/VP）')

# 海上建筑条目：声明州 → 海省新州
import numpy as np
from PIL import Image
rgb2id = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)

BP = os.path.join(G, 'map', 'buildings.txt')
lines = open(BP, encoding='utf-8-sig', newline='').read().split('\r\n')
fixed = 0
for i, l in enumerate(lines):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    xi, yi = int(round(float(f[2]))), int(round(H - float(f[4])))
    if not (0 <= xi < W and 0 <= yi < H):
        continue
    p = int(prov[yi, xi])
    if p in p2s_new:
        f[0] = str(p2s_new[p])
        lines[i] = ';'.join(f)
        fixed += 1
open(BP, 'w', encoding='utf-8', newline='').write('\r\n'.join(lines))
print(f'buildings.txt 海上条目修正 {fixed} 条')

# 复验
ids = collections.Counter()
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    ids[sid] += 1
dups = [s for s, n in ids.items() if n > 1]
print(f'复验: 州文件 {sum(ids.values())} 个 / 重复 id {len(dups)} {dups[:5]} / id 范围 {min(ids)}-{max(ids)}')
print(f'备份: {bdir}')

# -*- coding: utf-8 -*-
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
MAJ = ['MOT', 'LYY', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
DISPLAY = ['LYY', 'SUM', 'MOT', 'INA', 'FON', 'NAT', 'NDK', 'SNE']
o = []

cd = os.path.join(REPO, 'common', 'countries')
files = sorted(os.listdir(cd))
o.append(f'common/countries 文件 {len(files)} 个；每个文件的 tag:')
tag2file = {}
for i, f in enumerate(files):
    t = io.open(os.path.join(cd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    tags = re.findall(r'(?m)^\s*([A-Z]{3})\s*=\s*\{', t)
    o.append(f'  #{i}: {f} -> {tags}')
    for tg in tags:
        tag2file.setdefault(tg, f)

o.append('')
o.append('===== 八大国在 common/countries 的文件与顺序位置 =====')
pos = {}
for i, f in enumerate(files):
    for tg in MAJ:
        if tag2file.get(tg) == f:
            pos[tg] = i
o.append(f'  位置: {pos}')
o.append(f'  按显示顺序的位置: {[pos.get(t, -1) for t in DISPLAY]}')
o.append(f'  按显示顺序单调递增={all(pos.get(DISPLAY[i],-1) <= pos.get(DISPLAY[i+1],-1) for i in range(7))}')
o.append(f'  文件: {[(t, tag2file.get(t)) for t in MAJ]}')
print('\n'.join(o))

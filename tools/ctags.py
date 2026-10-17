# -*- coding: utf-8 -*-
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
MAJ = ['MOT', 'LYY', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
DISPLAY = ['LYY', 'SUM', 'MOT', 'INA', 'FON', 'NAT', 'NDK', 'SNE']
o = []

# 1) country_tags 注册顺序
for fp in glob.glob(os.path.join(REPO, 'common', 'country_tags', '*.txt')):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    tags = re.findall(r'(?m)^\s*([A-Z]{3})\s*=\s*"', t)
    o.append(f'{os.path.basename(fp)}: {len(tags)} 个 tag')
    idx = {tg: i for i, tg in enumerate(tags)}
    o.append(f'  八大国注册顺序: {[(tg, idx.get(tg)) for tg in MAJ]}')
    seq = [(tg, idx.get(tg, -1)) for tg in MAJ]
    o.append(f'  按显示顺序的注册号: {[idx.get(tg, -1) for tg in DISPLAY]} 单调递增={all(idx.get(DISPLAY[i],-1) <= idx.get(DISPLAY[i+1],-1) for i in range(7))}')

# 2) 所有 tag 的注册顺序全表位置检查
o.append('')
o.append('===== 其它可能的"国家注册/枚举"文件 =====')
for pat in ('common/countries', 'common/country_tag_aliases', 'common/country_creation'):
    d = os.path.join(REPO, pat.replace('/', os.sep))
    if os.path.isdir(d):
        fs = sorted(os.listdir(d))
        o.append(f'  {pat}: {len(fs)} 个: {fs[:10]}')
    else:
        o.append(f'  {pat}: 不存在')

# 3) 显示顺序 vs tag 的字母序
o.append('')
o.append(f'显示顺序: {DISPLAY}')
o.append(f'字母序: {sorted(MAJ)}')
o.append(f'反向字母序: {sorted(MAJ, reverse=True)}')
print('\n'.join(o))

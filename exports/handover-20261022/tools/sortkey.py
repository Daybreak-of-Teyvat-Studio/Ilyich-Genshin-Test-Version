# -*- coding: utf-8 -*-
"""找选国界面真实排序键：对比各国 州数/最低州号/首都/人力/省数 vs 显示顺序"""
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
o = []
MAJ = ['MOT', 'LYY', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
DISPLAY = ['LYY', 'SUM', 'MOT', 'INA', 'FON', 'NAT', 'NDK', 'SNE']   # 用户看到的顺序

sd = os.path.join(REPO, 'history', 'states')
info = {t: {'states': [], 'manpower': 0, 'provinces': 0, 'capital': None} for t in MAJ}
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'owner\s*=\s*(\w+)', t)
    if not m or m.group(1) not in info:
        continue
    tag = m.group(1)
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    info[tag]['states'].append(sid)
    mm = re.search(r'manpower\s*=\s*(\d+)', t)
    if mm:
        info[tag]['manpower'] += int(mm.group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    if pm:
        info[tag]['provinces'] += len(pm.group(1).split())

for fp in glob.glob(os.path.join(REPO, 'history', 'countries', '*.txt')):
    base = os.path.basename(fp)
    tag = base.split(' ')[0].strip()
    if tag in info:
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        cm = re.search(r'capital\s*=\s*(\d+)', t)
        if cm:
            info[tag]['capital'] = int(cm.group(1))

o.append('===== 八大国数据 =====')
for tag in MAJ:
    d = info[tag]
    o.append(f'  {tag}: 州数={len(d["states"])}, 最低州号={min(d["states"]) if d["states"] else "?"}, '
             f'首都={d["capital"]}, 人力={d["manpower"]}, 省数={d["provinces"]}')
    o.append(f'       州={sorted(d["states"])}')

o.append('')
o.append(f'显示顺序: {DISPLAY}')
o.append('===== 各候选排序键按显示顺序是否单调 =====')
def check(name, vals):
    seq = [vals[t] for t in DISPLAY]
    mono = all(seq[i] <= seq[i+1] for i in range(len(seq)-1))
    o.append(f'  {name}: {seq} 按显示顺序单调递增={mono}')

check('州数', {t: len(info[t]['states']) for t in MAJ})
check('最低州号', {t: (min(info[t]['states']) if info[t]['states'] else -1) for t in MAJ})
check('首都州号', {t: (info[t]['capital'] if info[t]['capital'] else -1) for t in MAJ})
check('人力', {t: info[t]['manpower'] for t in MAJ})
check('省数', {t: info[t]['provinces'] for t in MAJ})

# 国家文件/注册顺序（common/countries 文件名顺序）
o.append('')
o.append('===== common/countries 文件顺序（八大国所在位置） =====')
cd = os.path.join(REPO, 'common', 'countries')
files = sorted(os.listdir(cd)) if os.path.isdir(cd) else []
for i, f in enumerate(files):
    tag = f.split(' ')[0].strip()
    if tag in MAJ:
        o.append(f'  #{i}: {f}')
print('\n'.join(o))

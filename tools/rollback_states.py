# -*- coding: utf-8 -*-
"""回退：恢复 851-859、900；删除 9 个合并源空州文件。完成后 1-902 除合并源空号外完整。"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
ST = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')
B2 = os.path.join(ROOT, '.backups', 'fill_gaps_20260929_200011')

safety = os.path.join(ROOT, '.backups', 'pre_redo_' +
                      datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(safety, exist_ok=True)

# 0) 备份当前全部州文件（安全网）
for f in os.listdir(ST):
    if f.endswith('.txt'):
        shutil.copy2(os.path.join(ST, f), os.path.join(safety, f))
print(f'0) 当前状态已整体备份 {safety}')

# 1) 恢复 851-859（8 个满文件 + 856 空备份跳过）
for sid in (851, 852, 853, 854, 855, 856, 857, 858, 859):
    src = os.path.join(B2, f'{sid}-State_{sid}.txt')
    t = open(src, encoding='utf-8-sig', errors='replace').read()
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if not pm or not pm.group(1).split():
        print(f'  856 备份为空，跳过（该号留给补号）')
        continue
    shutil.copy2(src, os.path.join(ST, f'{sid}-State_{sid}.txt'))
    print(f'  恢复 {sid}（{len(pm.group(1).split())} 省）')

# 2) __tmp_900__ → 900（暗之外海）
tp = os.path.join(ST, '__tmp_900__.txt')
t = open(tp, encoding='utf-8-sig', newline='').read()
t = re.sub(r'(\bid\s*=\s*)\d+', r'\g<1>900', t, count=1)
t = re.sub(r'(\bname\s*=\s*")DOT_STATE_\d+(")', r'\g<1>DOT_STATE_900\g<2>', t, count=1)
open(os.path.join(ST, '900-State_900.txt'), 'w', encoding='utf-8', newline='').write(t)
os.remove(tp)
print('2) __tmp_900__ → 900-State_900.txt（暗之外海 845 省）')

# 3) 删除 9 个合并源空州文件
removed = []
for f in list(os.listdir(ST)):
    if not re.match(r'^\d+-', f):
        if f.startswith('__tmp'):
            os.remove(os.path.join(ST, f))
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if not pm or not pm.group(1).split():
        removed.append(f)
        os.remove(os.path.join(ST, f))
print(f'3) 删除空州文件 {len(removed)} 个: {sorted(removed)}')

# 4) 现状
ids = sorted(int(re.match(r'^(\d+)-', f).group(1)) for f in os.listdir(ST)
             if re.match(r'^\d+-', f))
holes = sorted(set(range(1, max(ids) + 1)) - set(ids))
print(f'\n现状: 州 {len(ids)} 个，1-{max(ids)}，缺号 {len(holes)}: {holes}')
print(f'总耗时 OK')

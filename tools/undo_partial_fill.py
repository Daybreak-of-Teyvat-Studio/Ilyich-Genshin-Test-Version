# -*- coding: utf-8 -*-
"""undo_partial_fill.py —— 撤销半执行的 fill_state_gaps
从 fill_out.txt 解析方案；已执行对（目标号 < 708）从 fill 备份还原原文件；
删除残留 __tmp_*.txt；终验 750 文件/1-890/SNE 65"""
import os, re, sys, glob, shutil

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
FILL_BD = os.path.join(ROOT, '.backups', 'fill_gaps_20261007_223112')

t = open(os.path.join(ROOT, 'tools', 'fill_out.txt'), encoding='utf-8-sig').read()
pairs = [(int(a), int(b)) for a, b in re.findall(r'state (\d+) .{0,3}state (\d+)', t)]
print(f'方案 {len(pairs)} 对')
executed = [(old, new) for old, new in pairs if new < 708]
print(f'已执行（目标<708）: {len(executed)} 对')

restored = 0
for old, new in executed:
    hole_f = os.path.join(ST, f'{new}-State_{new}.txt')
    src = os.path.join(FILL_BD, f'{old}-State_{old}.txt')
    assert os.path.exists(src), f'备份缺 {old}'
    if os.path.exists(hole_f):
        os.remove(hole_f)
    shutil.copy2(src, os.path.join(ST, f'{old}-State_{old}.txt'))
    restored += 1
print(f'还原 {restored} 个搬出者原文件')

for f in glob.glob(os.path.join(ST, '__tmp_*.txt')):
    os.remove(f)
    print(f'删除残留 {os.path.basename(f)}')

# 终验
fs = glob.glob(os.path.join(ST, '*.txt'))
ids = sorted(int(re.match(r'(\d+)-', os.path.basename(f)).group(1))
             for f in fs if re.match(r'\d+-', os.path.basename(f)))
holes = sorted(set(range(ids[0], ids[-1] + 1)) - set(ids))
sne = sum(1 for f in fs if 'owner = SNE' in open(f, encoding='utf-8-sig', errors='replace').read())
mis = [f for f in fs if (m := re.match(r'(\d+)-', os.path.basename(f))) and
       (c := re.search(r'\bid\s*=\s*(\d+)', open(f, encoding='utf-8-sig', errors='replace').read()))
       and int(m.group(1)) != int(c.group(1))]
print(f'终验: 文件 {len(fs)}，范围 {ids[0]}-{ids[-1]}，缺号 {len(holes)}，SNE {sne}，文件名/id 不一致 {len(mis)}')
print('缺号:', holes)

# -*- coding: utf-8 -*-
"""variant_gap.py —— PRI/INA/FAV：OOB 用到的舰体 vs 国家文件已有的变体"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

for tag in ('PRI', 'INA', 'FAV'):
    print(f'===== {tag} =====')
    # OOB（陆军+海军）用到的舰体类型
    used = collections.Counter()
    for f in glob.glob(os.path.join(G, 'history', 'units', f'{tag}_*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(r'equipment = \{\s*(ship_hull_\w+)', t):
            used[m.group(1)] += 1
    print('  OOB 用到的舰体:', dict(used))
    # 国家文件已有变体
    cf = glob.glob(os.path.join(G, 'history', 'countries', f'{tag} *.txt')) + \
         glob.glob(os.path.join(G, 'history', 'countries', f'{tag}-*.txt'))
    if cf:
        t = open(cf[0], encoding='utf-8-sig', errors='replace').read()
        variants = re.findall(r'name = "([^"]+)"\s*\r?\n\s*type = (ship_hull_\w+)', t)
        print(f'  {os.path.basename(cf[0])} 已有变体: {variants}')
    else:
        print('  国家文件: 未找到')
    print()

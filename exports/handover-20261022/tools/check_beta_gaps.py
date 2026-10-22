# -*- coding: utf-8 -*-
"""check_beta_gaps.py —— beta 版里是否存在 gamma 缺失的文件/变体"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== 缺失 OOB 文件：beta vs gamma ===')
for f in ('FAV_1936_air.txt', 'FON_air_bba.txt', 'LAW_1936_air.txt', 'MOT_1936_air.txt',
          'VAN_1936_air.txt', 'VAN_1936_naval.txt', 'PRI_1936_Naval.txt', 'INA_1936_Naval.txt'):
    b = os.path.exists(os.path.join(B, 'history', 'units', f))
    g = os.path.exists(os.path.join(G, 'history', 'units', f))
    print(f'  {f}: beta={"有" if b else "无"}（{os.path.getsize(os.path.join(B, "history", "units", f)) if b else 0}B） gamma={"有" if g else "无"}')

print()
print('=== beta 里 INA/FAV/LAW 的变体（国家文件）===')
for tag in ('INA', 'FAV', 'LAW', 'PRI'):
    for base, lbl in ((B, 'beta'), (G, 'gamma')):
        cfs = glob.glob(os.path.join(base, 'history', 'countries', f'{tag} *.txt')) + \
              glob.glob(os.path.join(base, 'history', 'countries', f'{tag}-*.txt'))
        if not cfs:
            print(f'  [{lbl}] {tag}: 国家文件未找到')
            continue
        t = open(cfs[0], encoding='utf-8-sig', errors='replace').read()
        vs = re.findall(r'name = "([^"]+)"\s*\r?\n\s*type = (\w+)', t)
        print(f'  [{lbl}] {tag}（{os.path.basename(cfs[0])}）: {len(vs)} 个变体')
        for n, ty in vs:
            print(f'      {n} | {ty}')

# -*- coding: utf-8 -*-
"""check_third_copy.py —— 扫描 'Ilyich Genshin Test Version' 副本的州健康度"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for cand in ('Ilyich Genshin Test Version', '.'):
    base = os.path.join(ROOT, cand)
    print(f'=== {cand} 顶层 ===')
    if os.path.isdir(base):
        fs = os.listdir(base)
        print(' ', fs[:25])
        st = os.path.join(base, 'history', 'states')
        if os.path.isdir(st):
            bfs = glob.glob(os.path.join(st, '*.txt'))
            print(f'  history/states: {len(bfs)} 个文件')
            n_own = n_landless = n_empty = 0
            for f in bfs:
                t = open(f, encoding='utf-8-sig', errors='replace').read()
                if not re.search(r'\bowner\s*=', t):
                    n_own += 1
                pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
                if pm is not None and not pm.group(1).split():
                    n_empty += 1
            print(f'  无 owner: {n_own}，空省: {n_empty}')
        else:
            print('  无 history/states')
    else:
        print('  不存在或已并入')
    print()

# -*- coding: utf-8 -*-
"""find_orphan_home.py —— 查 5 个孤儿省批次前的归属州"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
BK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  '.backups', 'states_20261007_222357', 'history', 'states')
for pid in (478, 1204, 1500, 1869, 3766):
    hits = []
    for f in glob.glob(os.path.join(BK, '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        if pm and re.search(r'\b' + str(pid) + r'\b', pm.group(1)):
            sid = re.search(r'\bid\s*=\s*(\d+)', t).group(1)
            om = re.search(r'\bowner\s*=\s*(\w+)', t)
            hits.append(f's{sid} owner={om.group(1) if om else "海"}')
    print(f'p{pid} 批次前: ' + (', '.join(hits) if hits else '无归属'))

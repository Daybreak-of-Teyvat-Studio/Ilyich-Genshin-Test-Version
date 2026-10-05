# -*- coding: utf-8 -*-
"""find_host.py —— 查省所在州与 owner"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  'Daybreak of Teyvat Gamma Version', 'history', 'states')
for pid in (4135, 4315):
    hits = []
    for f in glob.glob(os.path.join(ST, '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        if pm and re.search(r'\b' + str(pid) + r'\b', pm.group(1)):
            sid = re.search(r'\bid\s*=\s*(\d+)', t).group(1)
            om = re.search(r'\bowner\s*=\s*(\w+)', t)
            hits.append(f's{sid} owner={om.group(1) if om else "海"}')
    print(f'p{pid}: ' + (', '.join(hits) if hits else '不在任何州'))

# -*- coding: utf-8 -*-
"""check_00_backup.py —— :00 是否历史遗留（对照换位前备份）"""
import re, sys

sys.stdout.reconfigure(encoding='utf-8')
for tag, p in (('10-07备份', r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups\states_20261007_222357\DOT_state_names_gamma_l_simp_chinese.yml'),
               ('10-08备份', r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups\tower1314_20261008_130216\DOT_state_names_gamma_l_simp_chinese.yml')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    hits = [l.strip()[:70] for l in t.splitlines() if re.match(r'^\s*DOT_STATE_(708|750)\s*:', l)]
    print(tag, '::', hits)

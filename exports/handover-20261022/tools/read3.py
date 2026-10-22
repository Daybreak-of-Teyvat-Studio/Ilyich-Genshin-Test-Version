# -*- coding: utf-8 -*-
"""read3.py —— ①loc708精确行 ②LYY 90/94两处 ③62-67的province块"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== ① DOT_STATE_708/709 精确行 ===')
p = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
for l in open(p, encoding='utf-8-sig', errors='replace'):
    if re.match(r'\s*DOT_STATE_(708|709|89|90)\s*:', l):
        print(f'  {l.rstrip()!r}')

print()
print('=== ② LYY_scripted_effects 里全部 transfer_state = 90 / 94 ===')
p = os.path.join(G, 'common', 'scripted_effects', 'LYY_scripted_effects.txt')
ls = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
for i, l in enumerate(ls):
    if re.search(r'transfer_state\s*=\s*(90|94|89)\b', l):
        # 上文找 KQP/GYP 头
        ctx = ''
        for j in range(max(0, i - 6), i):
            if re.match(r'^\s*(KQP|GYP|LYY)\s*=\s*\{', ls[j]):
                ctx = ls[j].strip()
        print(f'  L{i+1}: {l.strip()!r}  (在 {ctx})')

print()
print('=== ③ 62/63/65/66/67 的 province 块 ===')
import glob
for sid in ('62', '63', '65', '66', '67'):
    fs = glob.glob(os.path.join(G, 'history', 'states', f'{sid}-*.txt'))
    if fs:
        t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
        blocks = re.findall(r'(?m)^\s*(\d+)\s*=\s*\{([^}]*)\}', t)
        print(f'  s{sid} ({os.path.basename(fs[0])}): 省块 {[(a, b.strip()) for a, b in blocks]}')

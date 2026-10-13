# -*- coding: utf-8 -*-
"""check_570.py —— 核查 state 570 + 六个海州键的原文行"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read().split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = c[4]
        except ValueError:
            pass

print('=== state 570 的画像 ===')
fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', '570*.txt'))
      if re.match(r'^570(\(|-)', os.path.basename(f))]
if fs:
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    print(f'  文件: {os.path.basename(fs[0])}')
    print('  ', t[:400].replace('\n', '\n   '))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    ps = [int(x) for x in re.findall(r'\d+', m.group(1))] if m else []
    print(f'  kind: {set(gk.get(p) for p in ps)}')
else:
    print('  ★无文件')

print()
print('=== gamma_l 中 570 与六个海州键的原文 ===')
p = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
raw = open(p, 'rb').read()
print(f'  BOM={raw[:3] == b"\xef\xbb\xbf"}')
ls = raw.decode('utf-8-sig', errors='replace').split('\n')
for i, l in enumerate(ls):
    m = re.match(r'\s*DOT_STATE_(\d+)\s*:', l)
    if m and int(m.group(1)) in (570, 740, 741, 744, 745, 747, 748, 136, 254, 574, 636, 695):
        print(f'  L{i+1}: {l.strip()!r}')

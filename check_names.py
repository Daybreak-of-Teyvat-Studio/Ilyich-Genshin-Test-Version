# -*- coding: utf-8 -*-
import os, re

B = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version'

names = set()
for fn in os.listdir(os.path.join(B, 'history', 'states')):
    if not fn.endswith('.txt'):
        continue
    t = open(os.path.join(B, 'history', 'states', fn), encoding='utf-8').read()
    m = re.search(r'name\s*=\s*"([^"]*)"', t)
    if m:
        names.add(m.group(1))
print('unique beta state names:', len(names))

for lang in ['simp_chinese', 'english']:
    lp = os.path.join(B, 'localisation', lang)
    if not os.path.isdir(lp):
        continue
    covered = set()
    for f in os.listdir(lp):
        t = open(os.path.join(lp, f), encoding='utf-8').read()
        for n in names:
            if re.search(r'^\s*' + re.escape(n) + r'\s*:\d+\s*"', t, re.M):
                covered.add(n)
    missing = [n for n in names if n not in covered]
    print('%s: covered %d / %d, missing %d' % (lang, len(covered), len(names), len(missing)))
    if lang == 'simp_chinese':
        print('  missing sample:', sorted(missing)[:50])

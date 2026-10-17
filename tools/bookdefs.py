# -*- coding: utf-8 -*-
import os, io, re, glob, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
hits = {}
for fp in glob.glob(os.path.join(REPO, '**', '*.txt'), recursive=True):
    if '.backups' in fp:
        continue
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for m in re.finditer(r'(?m)^\s*(Book_[A-Za-z0-9_]+)\s*=\s*\{', t):
        hits.setdefault(m.group(1), []).append(os.path.relpath(fp, REPO))
print('Book_ 定义数:', len(hits))
for k, v in sorted(hits.items()):
    print(' ', k, '->', v[:2])

# FAV 的名字
print('\nFAV 名字搜索:')
for fp in glob.glob(os.path.join(REPO, 'localisation', 'simp_chinese', '*.yml')):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for l in t.splitlines():
        if re.match(r'\s*FAV:', l) or re.match(r'\s*FAV_DEF:', l):
            print(' ', os.path.basename(fp), l.strip()[:100])

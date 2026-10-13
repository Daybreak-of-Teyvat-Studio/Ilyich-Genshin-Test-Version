# -*- coding: utf-8 -*-
"""scan_history.py —— 扫 history/ 全目录的六个号引用 + buildings.txt 残留排查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

SIX = ('740', '741', '744', '745', '747', '748')

print('=== ① history/ 全目录扫描六个号（任意语法）===')
found = []
for dirpath, dirnames, filenames in os.walk(os.path.join(G, 'history')):
    for fn in filenames:
        if not fn.endswith('.txt'):
            continue
        fp = os.path.join(dirpath, fn)
        rel = os.path.relpath(fp, G)
        t = open(fp, encoding='utf-8-sig', errors='replace').read()
        for i, l in enumerate(t.split('\n')):
            for num in SIX:
                if re.search(r'(?<![\d])' + num + r'(?![\d])', l):
                    # 排除纯数字 id 行（id = N / 省列表里的数字等）
                    if re.search(r'(?m)^\s*(id\s*=\s*' + num + r'|' + num + r'\s*$|' + num + r'\s)', l.strip()) and '=' not in l:
                        pass
                    found.append((rel, i + 1, num, l.strip()[:140]))

# 聚合展示（按文件）
cur, cnt = None, 0
for rel, ln, num, ctx in found:
    if rel != cur:
        print(f'\n--- {rel} ---')
        cur = rel
    print(f'  L{ln} [{num}]: {ctx}')
    cnt += 1
print(f'\n共 {cnt} 处')

print()
print('=== ② buildings.txt：col1 > 750 的残留行 / col1 = 六个号的 ===')
bp = os.path.join(G, 'map', 'buildings.txt')
over, six = 0, 0
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    p = l.split(';')
    if len(p) >= 2 and p[0].strip().isdigit():
        v = int(p[0])
        if v > 750:
            over += 1
            if over <= 5:
                print(f'  >750: {l.strip()[:110]}')
        if str(v) in SIX:
            six += 1
print(f'  col1 > 750 的行: {over}')
print(f'  col1 ∈ 六个号的行: {six}')

print()
print('=== ③ 六个陆地副本州的 buildings 行数（570/136/254/574/636/695）===')
need = {'570', '136', '254', '574', '636', '695'}
cnt2 = {}
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    p = l.split(';')
    if len(p) >= 2 and p[0].strip() in need:
        cnt2[p[0].strip()] = cnt2.get(p[0].strip(), 0) + 1
print(' ', cnt2)

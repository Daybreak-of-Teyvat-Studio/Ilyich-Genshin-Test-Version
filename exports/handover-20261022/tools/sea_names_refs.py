# -*- coding: utf-8 -*-
"""sea_names_refs.py —— 41 海州的 loc 名字 + 精确 mod 引用"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== 41 个海州的 loc 名字 ===')
allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()
for sid in list(range(709, 718)) + list(range(719, 751)):
    m = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    print(f'  {sid}: {m.group(1) if m else "★无"}')

print()
print('=== 精确：mod 文件里以 state 语法引用 709-750 的 ===')
PAT = re.compile(r'(?:state|owns_state|controls_state|transfer_state|owns|controls)\s*=\s*(7(?:0[9]|1[0-7]|1[9]|2\d|3\d|4\d|50))(?!\d)')
NOISE = re.compile(r'days\s*=\s*7|cost\s*=\s*7|=\s*7\d\d\s*#|[\d]+')  # 占位
real = []
for sub in ('common', 'events'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, *sub.split('/'))):
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for m in PAT.finditer(t):
                ctx = t[max(0, m.start() - 50):m.end() + 30].replace('\n', ' ')
                real.append((os.path.relpath(fp, G), m.group(1), ctx[:120]))
print(f'共 {len(real)} 处:')
seen = set()
for rel, num, ctx in real:
    k = (rel, num, ctx[:40])
    if k in seen:
        continue
    seen.add(k)
    print(f'  [{num}] {rel}: ...{ctx}...')

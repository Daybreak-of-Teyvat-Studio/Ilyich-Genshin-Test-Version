# -*- coding: utf-8 -*-
"""pin_mapping.py —— 钉死六个名字的错位关系 + 850-890 段的 loc 现状"""
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

# loc 全量
allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()

def loc_of(sid):
    m = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    return m.group(1) if m else '★无键'

def state_info(sid):
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{sid}*.txt'))
          if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    if not fs:
        return '★无文件'
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    ps = [int(x) for x in re.findall(r'\d+', m.group(1))] if m else []
    kinds = set(gk.get(p) for p in ps)
    ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
    return f'{len(ps)}省 kind={kinds} owner={ow.group(1) if ow else "-"}'

PAIRS = [(859, 740), (858, 741), (855, 744), (854, 745), (852, 747), (851, 748),
         (860, 739), (861, 738), (862, 737), (863, 736)]
print('=== 六对（旧|新 两边都看）===')
for a, b in PAIRS:
    print(f'  {a}: loc={loc_of(a):12s} | 内容: {state_info(a) if a <= 750 else "（无州文件，旧号）"}')
    print(f'  {b}: loc={loc_of(b):12s} | 内容: {state_info(b)}')
    print()

print('=== 850-890 段的 loc 键存在性 ===')
for sid in range(848, 892):
    v = loc_of(sid)
    if v != '★无键':
        print(f'  DOT_STATE_{sid} = {v}')
n = sum(1 for sid in range(848, 892) if loc_of(sid) != '★无键')
print(f'  共 {n} 个键存在')

print()
print('=== 278/279/282/284/289/290 的内容与名字（对端）===')
for sid in (278, 279, 280, 282, 284, 285, 288, 289, 290):
    print(f'  {sid}: loc={loc_of(sid):14s} {state_info(sid)}')

print()
print('=== 830-849 段的 loc（另一组低号对端）===')
for sid in (840, 841, 842, 843, 844, 845, 846):
    print(f'  {sid}: loc={loc_of(sid):12s} {state_info(sid)}')

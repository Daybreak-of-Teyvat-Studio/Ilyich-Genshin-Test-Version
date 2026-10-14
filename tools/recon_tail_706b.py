# -*- coding: utf-8 -*-
"""recon_tail_706b.py —— 按内容查 707/708/709 文件 + 无过滤引用扫描"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== ① history/states 里 id=706..709 的文件 ===')
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    if m and int(m.group(1)) in (706, 707, 708, 709):
        m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        ps = [int(x) for x in re.findall(r'\d+', m2.group(1))] if m2 else []
        ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
        man = re.search(r'manpower\s*=\s*(\d+)', t)
        nm = re.search(r'(?m)^\s*name\s*=\s*"([^"]*)"', t)
        print(f'  {os.path.basename(f)}: id={m.group(1)} name={nm.group(1) if nm else "-"} owner={ow.group(1) if ow else "-"} man={man.group(1) if man else "-"} 省{len(ps)}')

print()
print('=== ② 无过滤：706-709 token 全扫（仅统计每文件次数）===')
TOK = re.compile(r'(?<![\d])(706|707|708|709)(?![\d])')
EXCLUDE = ('resource_prospecting', '14_sea_on_actions', '12_wuw')
import collections
cnt = collections.Counter()
for sub in ('common', 'events', 'history'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        if 'states' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if any(x in rel for x in EXCLUDE):
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            n = len(TOK.findall(t))
            if n:
                cnt[rel] += n
for rel, n in cnt.most_common():
    print(f'  {rel}: {n}')

print()
print('=== ③ buildings 行数（707/708/709）===')
bp = os.path.join(G, 'map', 'buildings.txt')
cc = {}
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    c = l.split(';')
    if c and c[0].strip() in ('707', '708', '709'):
        cc[c[0].strip()] = cc.get(c[0].strip(), 0) + 1
print(f'  {cc}')

print()
print('=== ④ 706-709 各文件的 name= 键与注释 ===')
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    if m and int(m.group(1)) in (706, 707, 708, 709):
        nm = re.search(r'(?m)^\s*name\s*=\s*"([^"]*)"[^\n]*', t)
        print(f'  id={m.group(1)}: {nm.group(0).strip() if nm else "-"}  [{os.path.basename(f)}]')

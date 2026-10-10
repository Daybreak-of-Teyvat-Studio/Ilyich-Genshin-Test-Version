# -*- coding: utf-8 -*-
"""check_dva_files.py —— DVA 国家文件/部队/核心等专属内容的 beta 残留检查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== history/countries 里 DVA 文件 ===')
for p in glob.glob(os.path.join(G, 'history', 'countries', '*DVA*')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'--- {os.path.basename(p)} ---')
    for i, l in enumerate(t.splitlines(), 1):
        if re.search(r'capital|state|province|location|=\s*\d+', l):
            print(f'  {i}: {l.strip()[:120]}')

print()
print('=== history/units/DVA_1936.txt 全部 location 行 ===')
p = os.path.join(G, 'history', 'units', 'DVA_1936.txt')
if os.path.exists(p):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for i, l in enumerate(t.splitlines(), 1):
        if 'location' in l:
            print(f'  {i}: {l.strip()}')

print()
print('=== 哪些国家把州作为首都且首都州缺 owner/核心（复查） ===')
import collections
st_owner = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    co = re.findall(r'add_core_of\s*=\s*(\w+)', t)
    st_owner[sid] = (om.group(1) if om else None, co)
for p in sorted(glob.glob(os.path.join(G, 'history', 'countries', '*.txt'))):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    tag = os.path.basename(p).split(' ')[0].split('-')[0].strip()
    for m in re.finditer(r'(?m)^\s*capital\s*=\s*(\d+)', t):
        c = int(m.group(1))
        o, co = st_owner.get(c, (None, []))
        if o is None or (tag and tag not in co):
            print(f'  {os.path.basename(p)}: capital={c} owner={o} cores={co}')

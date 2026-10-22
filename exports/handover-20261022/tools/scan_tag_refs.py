# -*- coding: utf-8 -*-
"""scan_tag_refs.py —— tag 引用一致性
1) 30 个无主首都国家各自拥有多少州
2) 州文件里 owner / add_core_of 引用不存在的国家文件
3) 国家文件里的 tag 总数
"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# 存在国家文件的 tag
tags = {}
for p in glob.glob(os.path.join(G, 'history', 'countries', '*.txt')):
    tag = os.path.basename(p).split(' ')[0].split('-')[0].strip()
    if tag:
        tags.setdefault(tag, p)
print(f'国家文件 tag 数: {len(tags)}')

# 州归属统计
st_owner, st_cores, owned_count = {}, {}, collections.Counter()
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    o = om.group(1) if om else None
    st_owner[sid] = o
    if o:
        owned_count[o] += 1
    st_cores[sid] = re.findall(r'add_core_of\s*=\s*(\w+)', t)

print()
print('=== 30 个首都未拥有国家的领土数 ===')
CHECK = ['CHI', 'ENG', 'FOD', 'FOM', 'FRA', 'GER', 'GYP', 'HIL', 'HIP', 'HSR', 'HZH',
         'ITA', 'JAP', 'KQP', 'MHL', 'PBF', 'PRC', 'SFG', 'SFS', 'SGC', 'SGD', 'SHP',
         'SKD', 'SOV', 'SPI', 'USA', 'VLM', 'XXA', 'YLH', 'ZZZ']
for tag in CHECK:
    has_file = tag in tags
    print(f'  {tag}: 拥有州 {owned_count.get(tag, 0)}，国家文件 {"有" if has_file else "无"}')

print()
print('=== 州 owner 引用不存在的 tag ===')
bad_owner = [(s, o) for s, o in st_owner.items() if o and o not in tags]
print(f'  {len(bad_owner)}: {bad_owner[:20]}')

print()
print('=== add_core_of 引用不存在的 tag ===')
bad_core = [(s, c) for s, cs in st_cores.items() for c in cs if c not in tags]
print(f'  {len(bad_core)}: {bad_core[:20]}')

print()
print('=== 州无 owner 明细（复核）===')
no_own = sorted(s for s, o in st_owner.items() if not o)
print(f'  {len(no_own)}: {no_own}')

print()
print('=== 所有存在 tag 中拥有 0 州的国家 ===')
zero = [t for t in tags if owned_count.get(t, 0) == 0]
print(f'  {len(zero)}: {zero[:60]}')

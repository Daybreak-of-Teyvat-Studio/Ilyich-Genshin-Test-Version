# -*- coding: utf-8 -*-
import os, re
from collections import Counter

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\history\states'
files = [f for f in os.listdir(G) if f.endswith('.txt')]
print('total files:', len(files))

problems = []
res_nonempty = 0
res_empty = 0
no_name = 0
bld_prov_entries = 0
names = Counter()
cats = Counter()
res_totals = Counter()
for fn in files:
    t = open(os.path.join(G, fn), encoding='utf-8').read()
    if t.count('{') != t.count('}'):
        problems.append((fn, 'unbalanced', t.count('{'), t.count('}')))
    m = re.search(r'name = "([^"]*)"', t)
    if m:
        names[m.group(1)] += 1
    else:
        no_name += 1
    m = re.search(r'state_category = (\S+)', t)
    if m:
        cats[m.group(1)] += 1
    rb = re.search(r'resources = \{(.*?)\}', t, re.S)
    if rb:
        inner = rb.group(1).strip()
        if inner:
            res_nonempty += 1
            for k, v in re.findall(r'(\w+)\s*=\s*([\d.]+)', inner):
                res_totals[k] += float(v)
        else:
            res_empty += 1
    bb = re.search(r'buildings = \{(.*?)\}', t, re.S)
    if bb:
        bld_prov_entries += len(re.findall(r'\d+ = \{', bb.group(1)))

print('unbalanced problems:', len(problems), problems[:5])
print('no name:', no_name)
print('resources non-empty:', res_nonempty, '| empty:', res_empty)
print('province-specific building entries total:', bld_prov_entries)
print('unique names:', len(names))
print('top duplicated names:', names.most_common(10))
print('state_category dist:', dict(cats))
print('total resources (sum over all states):', dict(res_totals))

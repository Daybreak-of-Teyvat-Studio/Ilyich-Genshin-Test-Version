# -*- coding: utf-8 -*-
import os, re

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\history\states'
files = [f for f in os.listdir(G) if f.endswith('.txt')]

total_bld = 0
mismatch = 0
examples = []
for fn in files:
    t = open(os.path.join(G, fn), encoding='utf-8').read()
    # provinces
    pm = re.search(r'provinces = \{(.*?)\}', t, re.S)
    provs = set(re.findall(r'\d+', pm.group(1))) if pm else set()
    bb = re.search(r'buildings = \{(.*?)\}', t, re.S)
    if not bb:
        continue
    for bpid in re.findall(r'(\d+) = \{', bb.group(1)):
        total_bld += 1
        if bpid not in provs:
            mismatch += 1
            if len(examples) < 15:
                examples.append((fn, bpid, sorted(provs, key=int)[:8]))

print('total province-specific building entries:', total_bld)
print('entries whose province NOT in state provinces list:', mismatch)
for e in examples:
    print('  ', e)

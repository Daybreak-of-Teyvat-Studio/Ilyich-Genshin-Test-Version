# -*- coding: utf-8 -*-
"""extract_vanilla_variants.py —— 从原版提取 5 种舰体的合法变体块作模板"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
NEED = ['ship_hull_light_1', 'ship_hull_light_2', 'ship_hull_cruiser_1',
        'ship_hull_cruiser_2', 'ship_hull_heavy_2']
found = {}
for p in glob.glob(os.path.join(V, 'history', 'countries', '*.txt')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'create_equipment_variant\s*=\s*\{', t):
        depth, i = 0, m.end() - 1
        while i < len(t):
            if t[i] == '{':
                depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = t[m.start():i + 1]
        for need in NEED:
            if need not in found and re.search(r'type\s*=\s*' + need + r'\b', block):
                found[need] = (os.path.basename(p), block)
    if len(found) == len(NEED):
        break
for need in NEED:
    print(f'===== {need} ← {found[need][0] if need in found else "未找到"} =====')
    if need in found:
        print(found[need][1][:600])
    print()

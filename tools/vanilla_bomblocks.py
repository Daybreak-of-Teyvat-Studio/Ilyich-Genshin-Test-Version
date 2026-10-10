# -*- coding: utf-8 -*-
"""vanilla_bomblocks.py —— 原版 bomb_locks 变体的完整块与 type 对照"""
import re, sys

sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
for rel in ('history/countries/GER - Germany.txt', 'history/countries/ENG - Britain.txt'):
    p = V + '\\' + rel.replace('/', '\\')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'===== {rel} =====')
    n = 0
    for m in re.finditer(r'create_equipment_variant\s*=\s*\{', t):
        # 平衡提取块
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
        if 'bomb_locks' in block:
            n += 1
            if n <= 2:
                print(block[:700])
                print('---')
    print()

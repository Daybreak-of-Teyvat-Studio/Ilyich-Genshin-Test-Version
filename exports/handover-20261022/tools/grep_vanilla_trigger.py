# -*- coding: utf-8 -*-
"""grep_vanilla_trigger.py —— 看原版 has_full_control_of 的真实用法"""
import os, sys, re

sys.stdout.reconfigure(encoding='utf-8')
G = r'F:\Steam\steamapps\common\Hearts of Iron IV'
shown = 0
for dp, dn, fn in os.walk(os.path.join(G, 'common')):
    for f in fn:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(dp, f)
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(r'.{0,60}has_full_control_of.{0,60}', t):
            print(f'[{os.path.relpath(p, G)}] ...{m.group(0).strip()[:130]}')
            shown += 1
            if shown >= 15:
                sys.exit()

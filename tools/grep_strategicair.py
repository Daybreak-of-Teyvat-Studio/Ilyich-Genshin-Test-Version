# -*- coding: utf-8 -*-
"""grep_strategicair.py —— exe 里 strategicair.cpp 字符串块（选址检查的真实输入）"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
raw = open(os.path.join(V, 'hoi4.exe'), 'rb').read()
strs = [(m.start(), m.group(0).decode('ascii', errors='replace')) for m in re.finditer(rb'[\x20-\x7e]{5,}', raw)]

for kw in ('no air base site', 'no rocket site', 'no gun emplacement', 'air base site', 'strategicair'):
    idxs = [i for i, (o, s) in enumerate(strs) if kw in s]
    print(f'=== "{kw}": {len(idxs)} 段 ===')
    for i in idxs[:2]:
        off = strs[i][0]
        print(f'  @ {off:#x}')
        n = 0
        for o, s in strs:
            if abs(o - off) < 3000 and 'strategicair' not in s and len(s) < 220:
                if re.search(r'(?i)air|rocket|site|gun|state|province|map|building|define|error|base|emplace', s):
                    print(f'    {o:#x}: {s[:170]}')
                    n += 1
                    if n > 60:
                        break
    print()

# -*- coding: utf-8 -*-
"""dedup_state_keys.py —— 清理补号后的重复 DOT_STATE key
规则：同一 key 多行时，保留非 * 的真名行（搬迁州的名字）；全为 * 保留首行；双真名报人工"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES_F = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'localisation', 'simp_chinese',
                       'DOT_state_names_gamma_l_simp_chinese.yml')
raw = open(NAMES_F, 'rb').read()
has_bom = raw[:3] == b'\xef\xbb\xbf'
t = raw.decode('utf-8-sig')
nl = '\r\n' if '\r\n' in t else '\n'
lines = t.split(nl)
keyed = collections.defaultdict(list)
for i, l in enumerate(lines):
    m = re.match(r'^\s*DOT_STATE_(\d+):', l)
    if m:
        keyed[int(m.group(1))].append(i)
dups = {k: v for k, v in keyed.items() if len(v) > 1}
print(f'重复 key {len(dups)} 个')
drop = []
for k, idxs in dups.items():
    vals = [(i, re.match(r'^\s*DOT_STATE_\d+:\d*\s*"([^"]*)"', lines[i]).group(1)) for i in idxs]
    real = [i for i, v in vals if v != '*']
    if len(real) == 1:
        keep = real[0]
    elif len(real) == 0:
        keep = idxs[0]
    else:
        print(f'  !! key {k} 双真名: {vals} —— 保留首条真名，其余删（人工核对）')
        keep = real[0]
    for i in idxs:
        if i != keep:
            drop.append(i)
print(f'删除 {len(drop)} 行')
out = [l for i, l in enumerate(lines) if i not in set(drop)]
open(NAMES_F, 'wb').write(((b'\xef\xbb\xbf' if has_bom else b'') + nl.join(out).encode('utf-8')))
# 复验
t2 = open(NAMES_F, encoding='utf-8-sig').read()
c2 = collections.Counter(int(m.group(1)) for m in
                         re.finditer(r'^\s*DOT_STATE_(\d+):', t2, re.M))
d2 = {k: v for k, v in c2.items() if v > 1}
print(f'复验: 重复 key {len(d2)} 个 {"✓" if not d2 else "✗ " + str(d2)}')

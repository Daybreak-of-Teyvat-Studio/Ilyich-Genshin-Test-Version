# -*- coding: utf-8 -*-
import os, io, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\err149_out.txt'
o = []
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
lines = t.splitlines()

o.append('===== NOT WITHIN (149) 汇总 =====')
pairs = collections.Counter()
rows = []
for l in lines:
    m = re.search(r'error at line (\d+): map building\(([^)]*)\) location is not within specified state\. Supposed to be \'(\d+) - [^\']*\' but was \'(\d+) - ', l)
    if m:
        rows.append((int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))))
        pairs[(m.group(3), m.group(4))] += 1
o.append(f'  共 {len(rows)} 条；按 (旧→新) 统计:')
for (a, b), c in pairs.most_common(30):
    o.append(f'    {a} → {b}: {c}')
o.append('  前 12 条:')
for r in rows[:12]:
    o.append(f'    L{r[0]}: {r[1]} {r[2]} → {r[3]}')

o.append('')
o.append('===== INVALID STATE (74) =====')
inv = []
for l in lines:
    m = re.search(r'error at line (\d+): map building location has invalid state \((\d+)', l)
    if m:
        inv.append((int(m.group(1)), int(m.group(2))))
o.append(f'  共 {len(inv)} 条；state 值分布: {collections.Counter(v for _, v in inv)}')
for r in inv[:12]:
    o.append(f'    L{r[0]}: invalid state = {r[1]}')

o.append('')
o.append('===== coastal 相关行（9） =====')
for i, l in enumerate(lines, 1):
    if 'coastal' in l.lower():
        o.append(f'  L{i}: {l.strip()[:190]}')

# 抽看几行 buildings.txt 实际内容
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
raw = io.open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
bl = raw.split(b'\r\n')
o.append('')
o.append('===== 对应行实际内容（前 10 条 not-within + 前 6 条 invalid） =====')
for r in rows[:10]:
    o.append(f'  L{r[0]}: {bl[r[0]-1].decode("utf-8", "replace")[:80]}')
for r in inv[:6]:
    o.append(f'  L{r[0]}: {bl[r[0]-1].decode("utf-8", "replace")[:80]}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

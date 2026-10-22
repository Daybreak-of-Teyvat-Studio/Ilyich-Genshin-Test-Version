# -*- coding: utf-8 -*-
import os, io, re, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
OUT = os.path.join(REPO, 'tools', 'bldinspect_out.txt')
o = []

# 1) 从 error.log 提取完整报错
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
errs = []
for l in t.splitlines():
    if 'mapbuildings.cpp' in l and ('not within' in l or 'invalid state' in l or 'invalid arguments' in l):
        errs.append(l.strip())
o.append(f'===== nudge/游戏 buildings 报错 {len(errs)} 条（完整） =====')
for l in errs:
    o.append('  ' + l)

# 解析 (行号, 类型, 期望, 实际)
parsed = []
for l in errs:
    m = re.search(r'error at line (\d+): map building\(([^)]*)\) location is not within specified state\. Supposed to be \'(\d+) - ([^\']*)\' but was \'(\d+) - ([^\']*)\'for province (\d+)', l)
    if m:
        parsed.append((int(m.group(1)), m.group(2), int(m.group(3)), m.group(4), int(m.group(5)), m.group(6), int(m.group(7))))
o.append('')
o.append('===== 解析出的 14 条（行号/类型/期望州/实际州/省） =====')
for p in parsed:
    o.append(f'  L{p[0]}: {p[1]} 期望={p[2]}({p[3]}) 实际={p[4]}({p[5]}) 省={p[6]}')

# 2) 读 buildings.txt 对应行
fp = os.path.join(G, 'map', 'buildings.txt')
raw = io.open(fp, 'rb').read()
nl = b'\r\n' if b'\r\n' in raw else b'\n'
lines = raw.split(nl)
o.append('')
o.append(f'===== buildings.txt 共 {len(lines)} 行（1-based 对应） =====')
o.append('--- 14 条目标行 ---')
for p in parsed:
    idx = p[0] - 1
    if 0 <= idx < len(lines):
        o.append(f'  L{p[0]}: {lines[idx].decode("utf-8", "replace")!r}')
o.append('--- 损坏区 L39100-L39120 ---')
for i in range(39099, min(39120, len(lines))):
    o.append(f'  L{i+1}: {lines[i].decode("utf-8", "replace")!r}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

# -*- coding: utf-8 -*-
"""transfer_p47_s15.py v2 —— p47 s336 → s15（西风戍垒）
每步变更后用新鲜正则重搜（杜绝过期偏移拼接）；VP 值跨步传递；回读验证"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
BP = os.path.join(MOD, 'map', 'buildings.txt')
PID, DST = 47, 15


def history_close(t):
    m = re.search(r'\bhistory\s*=\s*\{', t)
    depth, i = 0, m.end() - 1
    while True:
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1


def load(p):
    return open(p, encoding='utf-8-sig', errors='replace').read()


def save(p, t):
    open(p, 'wb').write(t.encode('utf-8'))


vp_val = None
# ---- src: 移出省 + 摘除 VP ----
f = os.path.join(ST, f'336-State_336.txt')
t = load(f)
vpm = re.search(r'[ \t]*victory_points\s*=\s*\{\s*' + str(PID) + r'\s+(\d+)\s*\}[ \t]*\r?\n?', t)
if vpm:
    vp_val = vpm.group(1)
    t = t[:vpm.start()] + t[vpm.end():]
pm = re.search(r'(provinces\s*=\s*\{)([^}]*)(\})', t)          # VP 摘除后新鲜重搜
provs = pm.group(2).split()
provs.remove(str(PID))
t = t[:pm.start()] + pm.group(1) + '\r\n\t\t' + ' '.join(provs) + '\r\n\t' + pm.group(3) + t[pm.end():]
save(f, t)
print(f's336: p{PID} 移出，VP 值 {vp_val} 已捕获')

# ---- dst: 并入省 + 插入 VP ----
f = os.path.join(ST, f'{DST}-State_{DST}.txt')
t = load(f)
pm = re.search(r'(provinces\s*=\s*\{)([^}]*)(\})', t)
provs = pm.group(2).split()
provs.append(str(PID))
t = t[:pm.start()] + pm.group(1) + '\r\n\t\t' + ' '.join(provs) + '\r\n\t' + pm.group(3) + t[pm.end():]
if vp_val and f'victory_points = {{ {PID} ' not in t:
    close = history_close(t)
    ls = t.rfind('\n', 0, close) + 1
    t = t[:ls] + f'\t\tvictory_points = {{ {PID} {vp_val} }}\r\n' + t[ls:]
save(f, t)
print(f's{DST}: p{PID} 并入，VP {vp_val} 插入')

# ---- buildings 列 ----
raw = open(BP, 'rb').read()
nl = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl)
nb = 0
for i, l in enumerate(lines):
    f7 = l.split(';')
    if len(f7) == 7 and f7[6] == str(PID) and f7[0] == '336':
        f7[0] = str(DST)
        lines[i] = ';'.join(f7)
        nb += 1
open(BP, 'wb').write(nl.join(lines).encode('utf-8'))
print(f'buildings 同步 {nb} 条')

# ---- 回读验证（含括号平衡） ----
ok = True
for sid, want in ((336, False), (DST, True)):
    t = load(os.path.join(ST, f'{sid}-State_{sid}.txt'))
    has = re.search(r'provinces\s*=\s*\{[^}]*\b' + str(PID) + r'\b', t) is not None
    depth = 0
    for ch in t:
        depth += (ch == '{') - (ch == '}')
    bal = depth == 0
    ok &= (has == want) and bal
    print(f'  s{sid}: 含p{PID}={has}（应{want}）括号平衡={bal}')
print('验证' + ('通过 ✓' if ok else '失败 ✗'))

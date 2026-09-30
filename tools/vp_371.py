# -*- coding: utf-8 -*-
"""省 371：25 值 VP「先遣基地」+ 本地化 + set_capital（老规矩）。"""
import os, re, sys, shutil, datetime, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
CD = os.path.join(G, 'history', 'countries')

PID, CN, VAL = 371, '先遣基地', 25
s2p, s2o = {}, {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2o[sid] = re.search(r'\bowner\s*=\s*(\w+)', t).group(1)
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}
sid = p2s[PID]
tag = s2o[sid]
print(f'省 {PID} -> state {sid}（owner {tag}）')

bdir = os.path.join(ROOT, '.backups', 'vp_371_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)

# VP
fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
t = open(fp, encoding='utf-8-sig', newline='').read()
line = f'victory_points = {{ {PID} {VAL} }}'
if re.search(r'victory_points\s*=\s*\{[^}]*\}', t):
    t = re.sub(r'victory_points\s*=\s*\{[^}]*\}', line, t, count=1)
else:
    hm = re.search(r'\thistory = \{', t)
    depth, i, end = 0, hm.end() - 1, None
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
        i += 1
    ls = t.rfind('\r\n', 0, end) + 2
    t = t[:ls] + '\t\t' + line + '\r\n' + t[ls:]
with open(fp, 'w', encoding='utf-8', newline='') as fh:
    fh.write(t)
print(f'VP: {line}')

# set_capital
cdir = next(f for f in os.listdir(CD) if f.upper().startswith(tag))
fp2 = os.path.join(CD, cdir)
shutil.copy2(fp2, os.path.join(bdir, cdir))
t = open(fp2, encoding='utf-8-sig', newline='').read()
if re.search(r'(?m)^\s*capital\s*=', t):
    t2 = re.sub(r'(?m)^(\s*capital\s*=\s*)\d+', rf'\g<1>{sid}', t, count=1)
else:
    t2 = t.rstrip('\r\n') + f'\r\n\r\ncapital = {sid}\r\n'
with open(fp2, 'w', encoding='utf-8', newline='') as fh:
    fh.write(t2)
print(f'capital: {tag} = {sid}')

# 本地化
LOC = os.path.join(G, 'localisation', 'simp_chinese')
target = next((f for f in os.listdir(LOC) if 'victory' in f.lower() and f.endswith('.yml')),
              'DOT_Victory_Points_gamma_l_simp_chinese.yml')
lp = os.path.join(LOC, target)
cur = open(lp, encoding='utf-8-sig', errors='replace').read()
if f'VICTORY_POINTS_{PID}:' not in cur:
    add = f' VICTORY_POINTS_{PID}:0 "{CN}"'
    open(lp, 'wb').write((cur.rstrip('\r\n') + '\r\n' + add + '\r\n').encode('utf-8'))
    print(f'本地化：{target} 追加 VICTORY_POINTS_{PID}:0 "{CN}"')
else:
    print('本地化已存在')

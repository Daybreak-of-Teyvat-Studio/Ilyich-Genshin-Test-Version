# -*- coding: utf-8 -*-
"""finish_swap.py —— 完成 708↔750 换位
A) 回滚 KNA_decision / INA_Focus（鬼影格式改动）
B) 仓库：补完引用联动（修正版：只改真正换值的行，保留原格式）
C) 部署副本：全流程（州文件/首都/buildings/本地化/引用）
D) 终验：布局 + 双副本一致 + 括号自检"""
import os, re, sys, glob, shutil, hashlib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
MAP = {708: 750, 750: 708}
TOKEN = re.compile(r'\b(owns_state|controls_state|has_full_control_of_state|transfer_state|state|capital)\s*=\s*(\d+)\b')


def refs_pass(base, tag):
    n_files = n_edits = 0
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ('.backups', '.backup', '.git', '备份')]
        for f in files:
            if not f.endswith('.txt'):
                continue
            p = os.path.join(root, f)
            rr = os.path.relpath(p, base).replace('\\', '/')
            if rr.startswith('history/states') or rr == 'map/buildings.txt':
                continue
            raw = open(p, 'rb').read()
            try:
                t = raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                print(f'  [{tag}] 跳过非 UTF-8: {rr}')
                continue
            hits = [m for m in TOKEN.finditer(t) if int(m.group(2)) in MAP]

            def rep(m):
                nonlocal n_edits
                if int(m.group(2)) in MAP:
                    n_edits += 1
                    return m.group(1) + m.group(0)[len(m.group(1)):m.start(2) - m.start()] + str(MAP[int(m.group(2))])
                return m.group(0)
            t2 = TOKEN.sub(rep, t)
            if t2 != t:
                open(p, 'wb').write(((b'\xef\xbb\xbf' if raw[:3] == b'\xef\xbb\xbf' else b'') + t2.encode('utf-8')))
                n_files += 1
    print(f'[{tag}] 引用联动: {n_files} 文件 {n_edits} 处')


# A) 回滚两个鬼影文件（从部署副本=换位前原状）
for rel in ('common/decisions/KNA_decision.txt', 'common/national_focus/INA_Focus.txt'):
    shutil.copy2(os.path.join(DEP, *rel.split('/')), os.path.join(REPO, *rel.split('/')))
print('A) KNA_decision / INA_Focus 已还原')

# B) 仓库补完引用（修正版）
refs_pass(REPO, '仓库')

# C) 部署副本全流程
STd = os.path.join(DEP, 'history', 'states')
contents = {}
for sid in (708, 750):
    p = os.path.join(STd, f'{sid}-State_{sid}.txt')
    raw = open(p, 'rb').read()
    contents[sid] = (raw.decode('utf-8-sig'), raw[:3] == b'\xef\xbb\xbf')
for src, dst in MAP.items():
    t, bom = contents[src]
    t2 = re.sub(r'(\bid\s*=\s*)' + str(src) + r'\b', rf'\g<1>{dst}', t, count=1)
    t2 = t2.replace(f'name="DOT_STATE_{src}"', f'name="DOT_STATE_{dst}"')
    assert f'id = {dst}' in t2 and f'DOT_STATE_{dst}' in t2
    open(os.path.join(STd, f'{dst}-State_{dst}.txt'), 'wb').write(
        ((b'\xef\xbb\xbf' if bom else b'') + t2.encode('utf-8')))
print('C1) 副本州文件换位完成')

n_cap = 0
for p in glob.glob(os.path.join(DEP, 'history', 'countries', '*.txt')):
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    t2 = re.sub(r'(?m)^(\s*capital\s*=\s*)(\d+)',
                lambda m: m.group(0) if int(m.group(2)) not in MAP else m.group(1) + str(MAP[int(m.group(2))]), t)
    if t2 != t:
        open(p, 'wb').write(((b'\xef\xbb\xbf' if raw[:3] == b'\xef\xbb\xbf' else b'') + t2.encode('utf-8')))
        n_cap += 1
print(f'C2) 副本首都联动 {n_cap} 个文件')

bp = os.path.join(DEP, 'map', 'buildings.txt')
raw = open(bp, 'rb').read()
nl = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl)
n_b = 0
for i, l in enumerate(lines):
    f7 = l.split(';')
    if len(f7) == 7 and f7[0].isdigit() and int(f7[0]) in MAP:
        f7[0] = str(MAP[int(f7[0])])
        lines[i] = ';'.join(f7)
        n_b += 1
open(bp, 'wb').write(nl.join(lines).encode('utf-8'))
print(f'C3) 副本 buildings 列 {n_b} 条')

n_loc = 0
for p in glob.glob(os.path.join(DEP, 'localisation', 'simp_chinese', '*.yml')):
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    orig = t
    for src, dst in MAP.items():
        t = t.replace(f'DOT_STATE_{src}:', f'@@TMP_{dst}@@:')
    for src, dst in MAP.items():
        t = t.replace(f'@@TMP_{dst}@@:', f'DOT_STATE_{dst}:')
    if t != orig:
        open(p, 'wb').write(((b'\xef\xbb\xbf' if raw[:3] == b'\xef\xbb\xbf' else b'') + t.encode('utf-8')))
        n_loc += 1
print(f'C4) 副本本地化 {n_loc} 个文件')

refs_pass(DEP, '副本')

# D) 终验
print()
kind = {}
for l in open(os.path.join(REPO, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        kind[int(a[0])] = a[4]

def layout(base, tag):
    ST = os.path.join(base, 'history', 'states')
    sea, land = [], []
    for sid in range(705, 751):
        t = open(os.path.join(ST, f'{sid}-State_{sid}.txt'), encoding='utf-8-sig', errors='replace').read()
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        provs = [int(x) for x in (pm.group(1).split() if pm else [])]
        (sea if provs and all(kind.get(p) != 'land' for p in provs) else land).append(sid)
    print(f'{tag}: 海={sea}')
    print(f'      陆(705+)={land}')
    t = open(os.path.join(ST, '708-State_708.txt'), encoding='utf-8-sig').read()
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    print(f'      s708 owner={om.group(1)}')
    return sea, land

layout(REPO, '仓库')
layout(DEP, '副本')

print()
print('=== 双副本全树一致性 ===')
def tree(base):
    out = {}
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in ('.backups', '.backup', '__pycache__')]
        for f in fn:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, base)] = hashlib.md5(open(p, 'rb').read()).hexdigest()
    return out
tr, td = tree(REPO), tree(DEP)
diff = [k for k in set(tr) & set(td) if tr[k] != td[k]]
print(f'内容不同: {len(diff)} {diff[:12]}')
print(f'只在仓库 {len(set(tr)-set(td))}，只在副本 {len(set(td)-set(tr))}')

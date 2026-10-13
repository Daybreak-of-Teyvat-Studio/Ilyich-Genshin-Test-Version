# -*- coding: utf-8 -*-
"""audit_718_709.py —— 审计 718→709 重编号后的现场与残留引用（只读）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

print('=== ① 两个副本的州文件号段（头尾 + 数量）===')
for tag, base in (('仓库', G), ('副本', D)):
    fs = sorted(glob.glob(os.path.join(base, 'history', 'states', '*.txt')))
    ids = []
    for f in fs:
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
        if m:
            ids.append(int(m.group(1)))
    ids_s = sorted(ids)
    gaps = [i for i in range(1, max(ids_s) + 1) if i not in set(ids_s)]
    print(f'  {tag}: {len(fs)} 个文件, id {min(ids_s)}-{max(ids_s)}, 缺号 {gaps[:20]}')
    print(f'     700 段: {[i for i in ids_s if 690 <= i <= 720]}')

print()
print('=== ② 709-State_709.txt 全文 ===')
for tag, base in (('仓库', G),):
    fs = glob.glob(os.path.join(base, 'history', 'states', '709*.txt'))
    for f in fs:
        print(f'  --- {os.path.basename(f)} ---')
        print(open(f, encoding='utf-8-sig', errors='replace').read()[:900])

print()
print('=== ③ 残留 "718" 引用全树扫描（排除 .backups）===')
SEVEN = re.compile(r'(?<![\d])718(?![\d])')
for tag, base in (('仓库', G),):
    for sub in ('common', 'events', 'history', 'map', 'localisation'):
        for dirpath, dirnames, filenames in os.walk(os.path.join(base, sub)):
            if '.backups' in dirpath:
                continue
            for fn in filenames:
                if not fn.endswith(('.txt', '.yml', '.csv')):
                    continue
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, base)
                try:
                    t = open(fp, encoding='utf-8-sig', errors='replace').read()
                except Exception:
                    continue
                for i, l in enumerate(t.split('\n')):
                    if SEVEN.search(l):
                        if re.search(r'(?i)(days|cost|amount|value|year|expire)\s*=', l) and not re.search(r'state|owns|controls|transfer|capital|DOT_STATE|718=', l):
                            continue
                        print(f'  {rel} L{i+1}: {l.strip()[:140]}')

print()
print('=== ④ 关键点抽查 ===')
allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()
for sid in (709, 718):
    m = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    print(f'  loc DOT_STATE_{sid} = {m.group(1) if m else "★无键"}')
# buildings/airports/rocketsites 里的 709/718
bp = os.path.join(G, 'map', 'buildings.txt')
cnt = {709: 0, 718: 0}
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    c = l.split(';')
    if c and c[0].strip() in ('709', '718'):
        cnt[int(c[0])] += 1
print(f'  buildings.txt: 709 行={cnt[709]}, 718 行={cnt[718]}')
for fname in ('airports.txt', 'rocketsites.txt'):
    t = open(os.path.join(G, 'map', fname), encoding='utf-8-sig', errors='replace').read()
    has709 = bool(re.search(r'(?m)^\s*709\s*=', t))
    has718 = bool(re.search(r'(?m)^\s*718\s*=', t))
    print(f'  {fname}: 709键={has709} 718键={has718}')

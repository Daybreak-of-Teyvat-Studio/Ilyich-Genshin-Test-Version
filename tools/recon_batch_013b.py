# -*- coding: utf-8 -*-
"""recon_batch_013b.py —— ①SUM浪船机制的省份引用 ②特菈佐莉vs特拉佐莉 ③省4678/1233"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== ① SUM 浪船相关上下文 ===')
for rel, ln in (('common\\decisions\\SUM_decisions.txt', 238),
                ('common\\dynamic_modifiers\\SUM_dynamic_modifiers.txt', 75),
                ('common\\scripted_effects\\SUM_scripted_effects.txt', 52)):
    p = os.path.join(G, *rel.split('\\'))
    ls = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
    print(f'--- {rel} L{ln}±15 ---')
    for i in range(max(0, ln - 16), min(len(ls), ln + 14)):
        print(f'  L{i+1}: {ls[i].rstrip()[:130]}')
    print()

print('=== ①b SUM 文件里出现的 4 位省号候选（含 4678/1233 附近）===')
for rel in ('common\\decisions\\SUM_decisions.txt',
            'common\\scripted_effects\\SUM_scripted_effects.txt',
            'common\\dynamic_modifiers\\SUM_dynamic_modifiers.txt'):
    p = os.path.join(G, *rel.split('\\'))
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for num in ('4678', '1233'):
        for i, l in enumerate(t.split('\n')):
            if num in l:
                print(f'  [{num}] {rel} L{i+1}: {l.strip()[:130]}')

print()
print('=== ② 特菈佐莉 / 特拉佐莉 全树出现 ===')
for root2, dirnames, filenames in os.walk(G):
    if '.backups' in root2:
        continue
    for fn in filenames:
        if not fn.endswith('.yml'):
            continue
        fp = os.path.join(root2, fn)
        t = open(fp, encoding='utf-8-sig', errors='replace').read()
        for name in ('特菈佐莉', '特拉佐莉'):
            for m in re.finditer(name, t):
                i = t[:m.start()].count('\n') + 1
                ls = t.split('\n')
                print(f'  [{name}] {os.path.relpath(fp, G)} L{i}: {ls[i-1].strip()[:130]}')

print()
print('=== ③ 省 4678 / 1233 画像 ===')
gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read().split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = (c[4], c[5])
        except ValueError:
            pass
p2s = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        for pp in re.findall(r'\d+', m2.group(1)):
            p2s.setdefault(int(pp), int(m.group(1)))
allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()
for pid in (4678, 1233):
    k = gk.get(pid, ('?', '?'))
    st = p2s.get(pid)
    nm = re.search(rf'(?m)^\s*VICTORY_POINTS_{pid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    print(f'  省{pid}: kind={k[0]} coastal={k[1]} 属州={st} VP名={nm.group(1) if nm else "无"}')

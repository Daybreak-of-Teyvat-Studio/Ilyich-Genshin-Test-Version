# -*- coding: utf-8 -*-
"""recon_tail_706.py —— 尾部州 706-709 画像 + 全引用扫描（只读）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()

print('=== ① 尾部州 706-709 画像 ===')
for sid in (706, 707, 708, 709):
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{sid}*.txt'))
          if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    if not fs:
        print(f'  s{sid}: ★无文件')
        continue
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    ps = [int(x) for x in re.findall(r'\d+', m2.group(1))] if m2 else []
    man = re.search(r'manpower\s*=\s*(\d+)', t)
    lm = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    print(f'  s{sid} ({os.path.basename(fs[0])}): loc={lm.group(1) if lm else "★无"} owner={m.group(1) if m else "-"} man={man.group(1) if man else "-"} 省{len(ps)}: {ps[:12]}')

print()
print('=== ② 706-709 的全 token 引用（state 语法 + 裸作用域 + 其他）===')
TOK = re.compile(r'(?<![\d])(706|707|708|709)(?![\d])')
EXCLUDE = ('resource_prospecting', '14_sea_on_actions', '12_wuw')
n = 0
for sub in ('common', 'events', 'history'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        if 'states' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if any(x in rel for x in EXCLUDE):
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for i, l in enumerate(t.split('\n')):
                if TOK.search(l):
                    s = l.strip()
                    if re.search(r'(?i)(days|cost|amount|value|year|expire|manpower|hours)\s*=', s) and not re.search(r'(?i)state|owns|controls|transfer|capital|highlight|prioritize|targets', s):
                        continue
                    print(f'  {rel} L{i+1}: {s[:140]}')
                    n += 1
print(f'  共 {n} 处')

print()
print('=== ③ loc 里的 706-709 键 ===')
for sid in (706, 707, 708, 709):
    for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', t):
            print(f'  {os.path.basename(f)}: DOT_STATE_{sid} = {m.group(1)}')

print()
print('=== ④ buildings 行 / airports / rocketsites 键 ===')
bp = os.path.join(G, 'map', 'buildings.txt')
cnt = {}
for l in open(bp, encoding='utf-8-sig', errors='replace'):
    c = l.split(';')
    if c and c[0].strip() in ('706', '707', '708', '709'):
        cnt[c[0].strip()] = cnt.get(c[0].strip(), 0) + 1
print(f'  buildings 行数: {cnt}')
for fname in ('airports.txt', 'rocketsites.txt'):
    t = open(os.path.join(G, 'map', fname), encoding='utf-8-sig', errors='replace').read()
    for sid in (706, 707, 708, 709):
        m = re.search(rf'(?m)^\s*{sid}\s*=\s*\{{([^}}]*)\}}', t)
        print(f'  {fname} s{sid}: {m.group(1).strip() if m else "★无键"}')

print()
print('=== ⑤ 706-709 首都/奇观类引用 ===')
for sub in ('history', 'common'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        if 'states' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for i, l in enumerate(t.split('\n')):
                if re.search(r'(?i)(capital|wonder|奇观|landmark)\s*=\s*70[6789]\b', l):
                    print(f'  {os.path.relpath(fp, G)} L{i+1}: {l.strip()[:130]}')

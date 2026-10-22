# -*- coding: utf-8 -*-
"""final_pin.py —— ①六名字全 loc 出现 ②英文 loc 对端键 ③INA 陆地州名字"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

NAMES = ['知比山', '茂知祭场', '天云峠', '无想刃狭间', '蛇骨矿洞', '望泷村']

print('=== ① 六个名字在全部 loc 文件中的出现 ===')
for f in glob.glob(os.path.join(G, 'localisation', '**', '*.yml'), recursive=True):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    for nm in NAMES:
        for m in re.finditer(re.escape(nm), t):
            line = t[:m.start()].count('\n') + 1
            # 找该行的键
            ls = t.split('\n')
            ln = ls[line - 1] if line <= len(ls) else ''
            print(f'  [{os.path.relpath(f, G)}:{line}] {ln.strip()[:100]}')
print()

print('=== ② 英文 loc 中对端键与六名 ===')
for f in glob.glob(os.path.join(G, 'localisation', 'english', '*.yml')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    for sid in (278, 279, 282, 284, 289, 290, 740, 741, 744, 745, 747, 748):
        m = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:', t)
        if m:
            ls = t.split('\n')
            for l in ls:
                if re.match(rf'^\s*DOT_STATE_{sid}\s*:', l):
                    print(f'  [english/{os.path.basename(f)}] {l.strip()[:100]}')
                    break
    for nm in NAMES:
        if nm in t:
            for l in t.split('\n'):
                if nm in l:
                    print(f'  [english/{os.path.basename(f)}] {l.strip()[:100]}')
print()

print('=== ③ INA（稻妻）当前陆地州及其名字 ===')
n = 0
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
    if m and ow and ow.group(1) == 'INA':
        sid = int(m.group(1))
        allloc = ''
        for lf in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
            allloc += open(lf, encoding='utf-8-sig', errors='replace').read()
        mm = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
        nm = re.search(r'(?m)^\s*name\s*=\s*"([^"]*)"', t)
        m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        nps = len(re.findall(r'\d+', m2.group(1))) if m2 else 0
        print(f'  s{sid}: loc={mm.group(1) if mm else "★无"} name键={nm.group(1) if nm else "-"} {nps}省')
        n += 1
        if n > 40:
            break

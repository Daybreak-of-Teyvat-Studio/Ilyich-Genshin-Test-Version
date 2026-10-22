# -*- coding: utf-8 -*-
"""recon_batch_013.py —— 侦察：奥摩斯港浪船/4678、4219 VP、281/256 现状（只读）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== ① 搜 "奥摩斯港浪船" ===')
for root2, dirnames, filenames in os.walk(G):
    if '.backups' in root2:
        continue
    for fn in filenames:
        if not fn.endswith(('.txt', '.yml')):
            continue
        fp = os.path.join(root2, fn)
        t = open(fp, encoding='utf-8-sig', errors='replace').read()
        if '奥摩斯港浪船' in t or '奥摩斯港·浪船' in t:
            rel = os.path.relpath(fp, G)
            for i, l in enumerate(t.split('\n')):
                if '浪船' in l and '奥摩斯' in l:
                    print(f'  {rel} L{i+1}: {l.strip()[:160]}')

print()
print('=== ② 搜 "4678" 和 "1233"（浪船附近的上下文）===')
for root2, dirnames, filenames in os.walk(G):
    if '.backups' in root2:
        continue
    for fn in filenames:
        if not fn.endswith('.txt'):
            continue
        fp = os.path.join(root2, fn)
        t = open(fp, encoding='utf-8-sig', errors='replace').read()
        if '4678' in t:
            rel = os.path.relpath(fp, G)
            for i, l in enumerate(t.split('\n')):
                if '4678' in l:
                    print(f'  [4678] {rel} L{i+1}: {l.strip()[:150]}')

print()
print('=== ③ 4219 胜利点：州文件引用 + loc ===')
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    for i, l in enumerate(t.split('\n')):
        if re.search(r'victory_points\s*=\s*\{[^}]*\b4219\b', l):
            print(f'  {os.path.basename(f)} L{i+1}: {l.strip()[:140]}')
allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()
for m in re.finditer(r'(?m)^\s*VICTORY_POINTS_4219\s*:\s*\d*\s*"([^"]*)"', allloc):
    print(f'  VICTORY_POINTS_4219 = {m.group(1)}')

print()
print('=== ④ state 281 / 256 现状 ===')
for sid in (281, 256):
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{sid}*.txt'))
          if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    info = '无文件'
    if fs:
        t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
        m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        np_ = len(re.findall(r'\d+', m2.group(1))) if m2 else 0
        info = f'{os.path.basename(fs[0])} owner={m.group(1) if m else "-"} {np_}省'
    lm = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    print(f'  {sid}: loc={lm.group(1) if lm else "★无键"}  {info}')

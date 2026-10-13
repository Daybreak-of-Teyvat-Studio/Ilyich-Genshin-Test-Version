# -*- coding: utf-8 -*-
"""find_dialog_loc.py —— ①loc 文件里找弹窗文本 ②exe 里 IsMapInGoodState 上下文字符串"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV'

print('=== ① loc 搜弹窗文本 ===')
pats = ['user directory', 'integrity of game', 'load the map', 'map defition', 'Failed to load']
for base, tag in ((os.path.join(V, 'localisation'), '原版'), (os.path.join(G, 'localisation'), 'mod仓库'), (os.path.join(D, 'mod', 'Daybreak of Teyvat Gamma Version', 'localisation'), 'mod副本')):
    if not os.path.isdir(base):
        continue
    for f in glob.glob(os.path.join(base, '**', '*.yml'), recursive=True):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        for p in pats:
            if p.lower() in t.lower():
                for m in re.finditer(r'(?im)^.*' + re.escape(p).replace(' ', r'[\s_]*'), t):
                    print(f'  [{tag}] {os.path.relpath(f, base)}: {m.group(0).strip()[:160]}')

print()
print('=== ② exe: IsMapInGoodState 上下文 ===')
target = os.path.join(V, 'hoi4.exe')
raw = open(target, 'rb').read()
strs = [(m.start(), m.group(0).decode('ascii', errors='replace')) for m in re.finditer(rb'[\x20-\x7e]{5,}', raw)]
for kw in ('IsMapInGoodState', 'Map invalid'):
    idxs = [i for i, (o, s) in enumerate(strs) if kw in s]
    for i in idxs[:1]:
        off = strs[i][0]
        print(f'\n  --- "{kw}" @ {off:#x} 周边（±4000 字节窗口）---')
        n = 0
        for o, s in strs:
            if abs(o - off) < 4000:
                if re.search(r'(?i)map|state|province|error|fail|load|def', s) and len(s) < 200:
                    print(f'    {o:#x}: {s[:160]}')
                    n += 1
                    if n > 80:
                        break

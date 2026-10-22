# -*- coding: utf-8 -*-
"""final_sweep2.py —— 加载窗口全量行 + setup/system 日志 + entity 无前缀追查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'

print('=' * 70)
print('【A】error.log 22:51:14 - 22:51:40 全量行')
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
import collections
seq = collections.OrderedDict()
n = 0
for l in t.split('\n'):
    m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l)
    if not m:
        continue
    if '22:51:14' <= m.group(1) <= '22:51:40':
        n += 1
        k = re.sub(r'\d+', '#', re.sub(r'\[\w+\.cpp:\d+\]', '[]', l.strip()))[:150]
        if k not in seq:
            seq[k] = [0, l.strip()[:220]]
        seq[k][0] += 1
print(f'  窗口内 {n} 行 / {len(seq)} 类:')
for k, (cnt, sample) in seq.items():
    print(f'  ×{cnt:<5} {sample}')

print()
print('=' * 70)
print('【B】setup.log 尾部 30 行')
t = open(os.path.join(L, 'setup.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]
for l in lines[-30:]:
    print('  ', l.strip()[:180])

print()
print('=' * 70)
print('【C】system.log 尾部 20 行')
t = open(os.path.join(L, 'system.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]
for l in lines[-20:]:
    print('  ', l.strip()[:180])

print()
print('=' * 70)
print('【D】无前缀追查 entity: institute_of_tower / Lei_Line / research_center')
for tag, base in (('gamma', G), ('beta', B)):
    for pat in ('institute_of_tower', 'Lei_Line', 'research_center'):
        hits = []
        for dirpath, dirnames, filenames in os.walk(base):
            if any(x in dirpath for x in ('.git', '.backups')):
                continue
            for fn in filenames:
                if fn.endswith(('.txt', '.gfx', '.asset')):
                    fp = os.path.join(dirpath, fn)
                    try:
                        tt = open(fp, encoding='utf-8-sig', errors='replace').read()
                    except Exception:
                        continue
                    if pat in tt:
                        hits.append((os.path.relpath(fp, base), tt.count(pat)))
        print(f'  [{tag}] "{pat}": {hits[:8]}')

print()
print('=' * 70)
print('【E】原版 landmark 建筑定义样例（找 entity 行）')
for f in glob.glob(os.path.join(r'F:\Steam\steamapps\common\Hearts of Iron IV', 'common', 'buildings', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    if 'landmark_' in t:
        names = re.findall(r'(?m)^\s*(landmark_\w+)\s*=\s*\{', t)
        ents = re.findall(r'(?m)^\s*entity\s*=\s*(\S+)', t)
        print(f'  {os.path.basename(f)}: {len(names)} 个 landmark, entity 行 {len(ents)} 个')
        for m in re.finditer(r'(?m)^\s*(landmark_\w+)\s*=\s*\{', t):
            nm = m.group(1)
            blk = t[m.end():m.end() + 900]
            e = re.search(r'(?m)^\s*entity\s*=\s*(\S+)', blk)
            print(f'     {nm}: entity={e.group(1) if e else "★无"}')
        break

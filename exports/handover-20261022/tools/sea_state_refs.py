# -*- coding: utf-8 -*-
"""sea_state_refs.py —— 海州(709-750)被引用的地方 + 一个海州全文"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

sea = set(range(709, 718)) | set(range(719, 751))

print('=== 一个海州全文（709）===')
fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', '709*.txt')) if re.match(r'^709(\(|-)', os.path.basename(f))]
if fs:
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    print(t[:500])

print()
print('=== mod 自研文件中引用海州号的（common / events / history(非states) / scripted） ===')
hits = []
for sub in ('common', 'events'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, *sub.split('/'))):
        for fn in filenames:
            if not fn.endswith(('.txt', '.gui')):
                continue
            fp = os.path.join(dirpath, fn)
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for m in re.finditer(r'(?<![\d])(7(?:0[9]|1[0-7]|1[9]|2\d|3\d|4\d|50))(?![\d])', t):
                hits.append((os.path.relpath(fp, G), m.group(1), t[max(0, m.start() - 60):m.end() + 40].replace('\n', ' ')[:110]))
print(f'共 {len(hits)} 处:')
seen = set()
for rel, num, ctx in hits:
    k = (rel, num)
    if k in seen:
        continue
    seen.add(k)
    print(f'  {rel} [{num}]: ...{ctx}...')
    if len(seen) > 30:
        break

print()
print('=== loc 里的海州键 ===')
n = 0
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'(?m)^\s*DOT_STATE_(7(?:0[9]|1[0-7]|1[9]|2\d|3\d|4\d|50))[^:]*:', t):
        print(f'  {os.path.basename(f)}: DOT_STATE_{m.group(1)}')
        n += 1
print(f'  共 {n} 个海州 loc 键（前 5 已列）') if n else print('  无')

print()
print('=== buildings.txt 里还有没有海州行 ===')
c = 0
for l in open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    p = l.split(';')
    if p and p[0].strip().isdigit() and int(p[0]) in sea:
        c += 1
print(f'  {c} 条')

print()
print('=== 州号表/脚本类：海州在 stateid 相关文件的出现 ===')
for f in ('docs/州号变动_20261007至冬重划.md',):
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        t = open(p, encoding='utf-8', errors='replace').read()
        for m in list(re.finditer(r'7(?:0[9]|1[0-7]|1[9]|2\d|3\d|4\d|50)', t))[:6]:
            print(f'  {f}: ...{t[max(0,m.start()-40):m.end()+30]}...')

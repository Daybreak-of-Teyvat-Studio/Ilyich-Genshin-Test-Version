# -*- coding: utf-8 -*-
"""landmark_diag.py —— 两个地标的放置/资产/原版约定全查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'

N1 = 'landmark_institute_of_tower'
N2 = 'landmark_Lei_Line_research_center'

print('=' * 70)
print('【A】谁放置了这两个地标（history/ 下全搜）')
for tag, base in (('gamma', G), ('beta', B)):
    for N in (N1, N2):
        hits = []
        for dirpath, dirnames, filenames in os.walk(os.path.join(base, 'history')):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                t = open(fp, encoding='utf-8-sig', errors='replace').read()
                if N in t:
                    hits.append((os.path.relpath(fp, base), t.count(N)))
        print(f'  [{tag}] {N}: {hits}')
print()

print('=' * 70)
print('【B】gamma interface/buildings/DOT_landmarks.gfx 全文')
p = os.path.join(G, 'interface', 'buildings', 'DOT_landmarks.gfx')
if os.path.exists(p):
    print(open(p, encoding='utf-8-sig', errors='replace').read())
else:
    print('  不存在!')
print()

print('=' * 70)
print('【C】mod 的 DOT landmark 资产目录')
for tag, base in (('gamma', G), ('beta', B)):
    for sub in ('gfx/models/DOT_landmarks', 'gfx/models/buildings/DOT_landmarks'):
        d = os.path.join(base, *sub.split('/'))
        if os.path.isdir(d):
            files = []
            for dirpath, dirnames, filenames in os.walk(d):
                for fn in filenames:
                    files.append(os.path.relpath(os.path.join(dirpath, fn), base))
            print(f'  [{tag}] {sub}: {len(files)} 个文件')
            for f in files[:20]:
                print(f'      {f}')
        else:
            print(f'  [{tag}] {sub}: 无')
print()

print('=' * 70)
print('【D】原版地标 entity 命名约定（找 kremlin / big_ben）')
for dirpath, dirnames, filenames in os.walk(V):
    if 'gfx' not in dirpath and 'interface' not in dirpath:
        continue
    for fn in filenames:
        if fn.endswith(('.asset', '.gfx')):
            fp = os.path.join(dirpath, fn)
            try:
                t = open(fp, encoding='utf-8-sig', errors='replace').read()
            except Exception:
                continue
            if 'kremlin' in t.lower() or 'big_ben' in t.lower():
                rel = os.path.relpath(fp, V)
                # 打出现场行
                for m in re.finditer(r'(?im)^.*(kremlin|big_ben).*$', t):
                    line = m.group(0).strip()[:140]
                    print(f'  {rel}: {line}')
                break
print()

print('=' * 70)
print('【E】原版 buildings.txt 里 landmark 行的样子（landmark_spawn 行的第7列）')
cnt = 0
for l in open(os.path.join(V, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if ';landmark_spawn;' in l or ';landmark_' in l:
        print('  ', l.strip()[:130])
        cnt += 1
        if cnt > 12:
            break
print()

print('=' * 70)
print('【F】gamma 有没有 landmark 相关行（buildings.txt）')
cnt = 0
for l in open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if 'landmark' in l.lower():
        print('  ', l.strip()[:130])
        cnt += 1
print(f'  共 {cnt} 行')

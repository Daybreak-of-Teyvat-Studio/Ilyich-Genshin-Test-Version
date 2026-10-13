# -*- coding: utf-8 -*-
"""landmark_fix_recon.py —— entity 块格式 + 字段支持 + 模组 sanghe 引用"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'

print('=' * 70)
print('【A】原版 gfx/entities/landmarks.asset 头 60 行')
p = os.path.join(V, 'gfx', 'entities', 'landmarks.asset')
t = open(p, encoding='utf-8-sig', errors='replace').read()
for l in t.split('\n')[:60]:
    print('  ', l.rstrip()[:150])

print()
print('=' * 70)
print('【B】原版 common/buildings 里有没有 entity = 字段')
found = False
for f in glob.glob(os.path.join(V, 'common', 'buildings', '*.txt')):
    t2 = open(f, encoding='utf-8-sig', errors='replace').read()
    ms = re.findall(r'(?m)^\s*entity\s*=\s*(\S+)', t2)
    if ms:
        print(f'  {os.path.basename(f)}: {len(ms)} 处 entity= , 例: {ms[:5]}')
        found = True
if not found:
    print('  ★ 原版建筑定义里没有 entity = 字段')

print()
print('=' * 70)
print('【C】原版 .asset 里 building_ 前缀 entity 名单（前 30）')
names = []
for f in glob.glob(os.path.join(V, 'gfx', 'entities', '*.asset')):
    t3 = open(f, encoding='utf-8-sig', errors='replace').read()
    names += re.findall(r'name\s*=\s*"(building_[^"]+)"', t3)
for n in names[:30]:
    print('  ', n)
print(f'  共 {len(names)} 个')

print()
print('=' * 70)
print('【D】gamma 里谁引用 sanghe / forbidden_city 的 mesh（找注册处）')
for pat in ('sanghe', 'landmark_forbidden_city_mesh', 'pdxmesh'):
    print(f'  --- "{pat}" ---')
    n = 0
    for dirpath, dirnames, filenames in os.walk(G):
        if any(x in dirpath for x in ('.git', '.backups')):
            continue
        for fn in filenames:
            if fn.endswith(('.asset', '.gfx', '.txt')):
                fp = os.path.join(dirpath, fn)
                try:
                    tt = open(fp, encoding='utf-8-sig', errors='replace').read()
                except Exception:
                    continue
                if pat in tt:
                    for m in re.finditer(r'(?im)^.*' + re.escape(pat) + r'.*$', tt):
                        print(f'    {os.path.relpath(fp, G)}: {m.group(0).strip()[:120]}')
                        n += 1
                        if n > 12:
                            break
            if n > 12:
                break
        if n > 12:
            break

print()
print('=' * 70)
print('【E】DVA_focustree 里两处引用上下文')
p = os.path.join(G, 'common', 'national_focus', 'DVA_focustree.txt')
t4 = open(p, encoding='utf-8-sig', errors='replace').read()
for N in ('landmark_institute_of_tower', 'landmark_Lei_Line_research_center'):
    for m in re.finditer(re.escape(N), t4):
        s = max(0, m.start() - 200)
        print(f'  --- {N} @ {m.start()} ---')
        print('   ', t4[s:m.end() + 100].replace('\n', '\n    ')[:400])
        break

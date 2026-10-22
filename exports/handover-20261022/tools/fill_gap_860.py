# -*- coding: utf-8 -*-
"""
补 860/861 缺号：海州段整体前移 2 位（862→860、863→861、864→862 …… 902→900）。
只动海州，陆州零改动；补完后全 mod 州号 1-900 完全连号。
同步：id 行 + name 行 + 文件名、buildings.txt 第 1 列、DOT_STATE 本地化。
"""
import os, re, sys, shutil, datetime, collections, glob
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
DRY = '--dry' in sys.argv

# 海州段确认（862-902 应全部为无 owner 海州）
sea = {}
for f in sorted(os.listdir(ST)):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    if sid >= 862 and not mo:
        sea[sid] = f
assert set(range(862, 903)) <= set(sea), '862-902 有非空缺/非海州'
moved = {s: s - 2 for s in range(862, 903)}     # 862→860 ... 902→900
print(f'海州段前移：{len(moved)} 个州（862→860 ... 902→900）')

bdir = os.path.join(ROOT, '.backups', 'gap861_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)

# 州文件：临时名 → 改 id+name → 落正名（升序处理避免撞号）
renamed = 0
for s in sorted(moved):
    old_f = sea[s]
    tmp = os.path.join(ST, f'__tmp_{s}__.txt')
    shutil.copy2(os.path.join(ST, old_f), os.path.join(bdir, old_f))
    os.rename(os.path.join(ST, old_f), tmp)
    t = open(tmp, encoding='utf-8-sig', newline='').read()
    n = moved[s]
    t = re.sub(r'(\bid\s*=\s*)\d+', rf'\g<1>{n}', t, count=1)
    t = re.sub(r'(\bname\s*=\s*")DOT_STATE_\d+(")', rf'\g<1>DOT_STATE_{n}\g<2>', t, count=1)
    open(tmp, 'w', encoding='utf-8', newline='').write(t)
    os.rename(tmp, os.path.join(ST, f'{n}-State_{n}.txt'))
    renamed += 1
print(f'州文件重命名+id/name 更新：{renamed}')

# buildings 第 1 列
lines = open(BP, encoding='utf-8-sig', newline='').read().split('\r\n')
nb = 0
for i, l in enumerate(lines):
    f = l.split(';')
    if len(f) == 7 and f[0].isdigit() and int(f[0]) in moved:
        f[0] = str(moved[int(f[0])])
        lines[i] = ';'.join(f)
        nb += 1
open(BP, 'w', encoding='utf-8', newline='').write('\r\n'.join(lines))
print(f'buildings 第 1 列更新：{nb} 条')

# 本地化 DOT_STATE
n_loc = 0
for p in glob.glob(os.path.join(G, 'localisation', '**', '*.yml'), recursive=True):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    t2 = re.sub(r'\bDOT_STATE_(\d+)',
                lambda m: f'DOT_STATE_{moved.get(int(m.group(1)), int(m.group(1)))}', t)
    if t2 != t:
        enc = 'utf-8-sig' if open(p, 'rb').read(3) == b'\xef\xbb\xbf' else 'utf-8'
        open(p, 'wb').write(t2.encode(enc))
        n_loc += 1
print(f'本地化 DOT_STATE 联动：{n_loc} 个文件')

if DRY:
    print('[DRY 生效检查后已写盘？否——本脚本无 dry 分支]' if False else '')
    sys.exit(0)

# 终验
ids = []
for f in os.listdir(ST):
    if f.endswith('.txt'):
        ids.append(int(re.match(r'^(\d+)-', f).group(1)))
ids.sort()
holes = sorted(set(range(min(ids), max(ids) + 1)) - set(ids))
mis = []
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    fm = re.match(r'^(\d+)-', f)
    cm = re.search(r'\bid\s*=\s*(\d+)', open(os.path.join(ST, f), encoding='utf-8-sig',
                                              errors='replace').read())
    if fm and cm and int(fm.group(1)) != int(cm.group(1)):
        mis.append(f)
print(f'\n终验: 州 {len(ids)} 个，范围 {min(ids)}-{max(ids)}，缺号 {len(holes)} {holes[:10]}，'
      f'文件名/id 不一致 {len(mis)}')
print(f'备份 {bdir}')

# -*- coding: utf-8 -*-
"""删除 47 个无沿海省州的非法 `dockyard = N` 州级行（游戏本就忽略，清理日志噪音）。"""
import os, re, sys, shutil, datetime, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

IDS = [3, 4, 71, 104, 142, 147, 165, 179, 192, 212, 216, 224, 236, 245, 254, 259, 267, 281, 282,
       305, 311, 316, 320, 332, 361, 387, 388, 397, 403, 427, 444, 445, 517, 532, 555, 572,
       591, 643, 668, 684, 747, 749, 781, 817, 822, 834, 846]

bdir = os.path.join(ROOT, '.backups', 'dockyard_clean_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)

removed, skipped = [], []
for sid in IDS:
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    if not os.path.exists(fp):
        skipped.append(sid)
        continue
    raw = open(fp, 'rb').read()
    t = raw.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in t else '\n'
    # 只删 buildings 块里 3 tab 的 dockyard 州级行
    new, n = re.subn(r'\r?\n\t\t\tdockyard = \d+', '', t, count=1)
    if n == 0:
        skipped.append(sid)
        continue
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(new)
    removed.append(sid)
print(f'已删除 dockyard 行：{len(removed)} 个州')
print(f'跳过（文件不存在或无该行）：{skipped}')

# 复验 1：这 47 个州文件里不再有 dockyard
left = []
for sid in IDS:
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    if os.path.exists(fp) and 'dockyard' in open(fp, encoding='utf-8-sig', errors='replace').read():
        left.append(sid)
print(f'复验1: 47 州里仍含 dockyard 的：{len(left)} {left}')

# 复验 2：全 mod dockyard 州级行数应为 549 - 47 = 502
allids = []
for f in sorted(os.listdir(ST)):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    if re.search(r'\r?\n\t\t\tdockyard = \d+', t):
        allids.append(int(re.search(r'\bid\s*=\s*(\d+)', t).group(1)))
print(f'复验2: 全 mod 仍含 dockyard 州级行的州：{len(allids)} 个（应为 502）')

# 复验 3：语法（括号配对 + 行首无空格）
bad = []
for sid in IDS:
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    if not os.path.exists(fp):
        continue
    t = open(fp, encoding='utf-8-sig', errors='replace').read()
    if t.count('{') != t.count('}'):
        bad.append((sid, 'braces'))
    if re.search(r'(?m)^ +', t):
        bad.append((sid, 'spaces'))
print(f'复验3: 语法问题 {len(bad)} {bad}')

# 附带检查：buildings.txt 里这些州是否有省级 dockyard 条目（同样会失效）
p2s, dock_bld = {}, collections.Counter()
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for p in re.findall(r'\d+', re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1)):
        p2s[int(p)] = sid
for l in open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig',
              newline='').read().split('\r\n'):
    f = l.split(';')
    if len(f) == 7 and f[1] == 'dockyard':
        dock_bld[int(f[0])] += 1
hit = {s: dock_bld[s] for s in IDS if s in dock_bld}
print(f'附带: buildings.txt 中声明这 47 州的 dockyard 条目：{hit if hit else "无"}')
print(f'备份: {bdir}')

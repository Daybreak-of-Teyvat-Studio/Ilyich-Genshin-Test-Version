# -*- coding: utf-8 -*-
"""full_analysis.py —— 只读：完整日志分类 + buildings 尾段结构 + INA OOB 全行"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'

print('=' * 70)
print('【A】live error.log 完整分类（按首现时间）')
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]
print(f'  总行数 {len(lines)}  首 {lines[0][:50]}')
groups = collections.OrderedDict()
for l in lines:
    m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l)
    ts = m.group(1) if m else '??'
    k = re.sub(r'\d+', '#', re.sub(r'\[\w+\.cpp:\d+\]', '[]', l.strip()))[:120]
    if k not in groups:
        groups[k] = [0, ts, l.strip()[:200]]
    groups[k][0] += 1
print(f'  分类数 {len(groups)}')
# 按模块归类统计
mod = collections.Counter()
mod_first = {}
for k, (n, ts, sample) in groups.items():
    m2 = re.search(r'\[([\w]+)\.(?:cpp|h):\d+\]', sample) or re.search(r'\[([\w]+)\.(?:cpp|h):\d+\]', k)
    name = m2.group(1) if m2 else 'other'
    mod[name] += n
    mod_first.setdefault(name, ts)
print('  按模块（行数）:')
for name, n in mod.most_common(40):
    print(f'    {name:38s} {n:>5}  (首现 {mod_first[name]})')

print()
print('=' * 70)
print('【B】mapbuildings.cpp 各子类统计')
mb = collections.Counter()
mb_first = {}
for l in lines:
    m = re.search(r'mapbuildings\.cpp:(\d+)\]: (.*)', l)
    if m:
        key = (m.group(1), re.sub(r'\d+', '#', m.group(2))[:80])
        mb[key] += 1
        if key not in mb_first:
            mb_first[key] = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l).group(1)
for (ln, msg), n in mb.most_common():
    print(f'  ×{n:<4} mapbuildings.cpp:{ln}  {msg}  (首现 {mb_first[(ln, msg)]})')

print()
print('=' * 70)
print('【C】buildings.txt 空行结构（invalid arguments count 根因）')
ls = open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8', errors='replace').read().split('\n')
blank_idx = [i + 1 for i, l in enumerate(ls) if not l.strip()]
print(f'  总行 {len(ls)}, 空行 {len(blank_idx)} 个')
if blank_idx:
    print(f'  空行行号（前 30）: {blank_idx[:30]}')
    print(f'  空行行号（后 10）: {blank_idx[-10:]}')
    # 空行区域
    runs = []
    start = prev = blank_idx[0]
    for b in blank_idx[1:]:
        if b == prev + 1:
            prev = b
        else:
            runs.append((start, prev))
            start = prev = b
    runs.append((start, prev))
    print(f'  空行区间 {len(runs)} 段: {runs[:20]}')
# 40753 的原始字节
raw = open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
# 找 40753 行（按 \n 计数）
pos = 0
for i in range(40753):
    pos = raw.find(b'\n', pos) + 1
end = raw.find(b'\n', pos)
print(f'  行40753 原始字节: {raw[pos:end]!r}')

print()
print('=' * 70)
print('【D】INA OOB 中 cruiser_2/light_2 舰的完整 version_name')
p = os.path.join(G, 'history', 'units', 'INA_1936_Naval.txt')
t2 = open(p, encoding='utf-8-sig', errors='replace').read()
for m in re.finditer(r'ship = \{[^}]*\}[^}]*\}[^}]*\}', t2):
    blk = m.group(0)
    if 'cruiser_2' in blk or 'light_2' in blk:
        print('  ', blk.replace('\n', ' ')[:260])
print()
p = os.path.join(G, 'history', 'units', 'FAV_1936_Naval.txt')
if os.path.exists(p):
    t3 = open(p, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'ship = \{[^}]*\}[^}]*\}[^}]*\}', t3):
        blk = m.group(0)
        if 'heavy_2' in blk or 'light_1' in blk:
            print(f'  FAV: {blk.replace(chr(10), " ")[:240]}')

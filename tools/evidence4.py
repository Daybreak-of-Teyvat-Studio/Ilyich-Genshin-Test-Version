# -*- coding: utf-8 -*-
"""evidence4.py —— 317 定性 + too many buildings 规则 + 文件被毁时间 + id 映射资产"""
import os, re, sys, glob, time, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

def load_def(base):
    kinds = {}
    p = os.path.join(base, 'map', 'definition.csv')
    for l in open(p, encoding='utf-8-sig', errors='replace'):
        c = l.strip().split(';')
        if len(c) >= 5:
            try:
                kinds[int(c[0])] = (c[4], c[5])
            except ValueError:
                pass
    return kinds

gd = load_def(G)
bd = load_def(B)

print('=' * 70)
print('【A】state 317 的省属性（gamma）')
prov317 = [202, 362, 1011, 1028, 2957, 2963, 2966, 2969, 2973, 2978, 2980]
for p in prov317:
    k = gd.get(p, ('不存在', ''))
    print(f'   {p}: {k[0]} coastal={k[1]}')
print()

print('=' * 70)
print('【B】317 在 buildings.txt 的行（类型 + 第7列）')
n = 0
for l in open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if l.strip().startswith('317;'):
        c = l.strip().split(';')
        print('   ', l.strip())
        n += 1
        if n > 30:
            break
print(f'   共 {n} 行')
print()

print('=' * 70)
print('【C】beta 海洋州(726-730)的机场选址省在原版的属性（beta definition）')
for p in (4003, 3697, 921, 1066, 3038):
    k = bd.get(p, ('不存在', ''))
    print(f'   {p}: kind={k[0]} coastal={k[1]}')
print()

print('=' * 70)
print('【D】四个被毁文件的 mtime')
for f in ('airports.txt', 'rocketsites.txt', 'supply_nodes.txt', 'railways.txt', 'buildings.txt'):
    for tag, base in (('副本', D), ('仓库', G)):
        p = os.path.join(base, 'map', f)
        if os.path.exists(p):
            mt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))
            print(f'   {tag} {f:20s} {mt}  {os.path.getsize(p):>10,}B')
print()

print('=' * 70)
print('【E】15 个 too many 州的 state 文件 buildings 块 vs 州类别')
bad = [76, 82, 223, 246, 269, 284, 311, 500, 560, 564, 569, 584, 587, 590, 607]

def level_sum(base, sid):
    fs = glob.glob(os.path.join(base, 'history', 'states', f'{sid}*.txt'))
    for f in fs:
        fn = os.path.basename(f)
        if not fn.startswith(str(sid)):
            continue
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'buildings\s*=\s*\{', t)
        if not m:
            return None, None, fn
        depth, i = 0, m.end() - 1
        while i < len(t):
            if t[i] == '{':
                depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blk = t[m.end():i]
        # 顶层 building = N 对（排除嵌套 province 块）
        tot = 0
        for bm in re.finditer(r'(?m)^\s*([a-z_]+)\s*=\s*(\d+)\s*$', blk):
            tot += int(bm.group(2))
        cat = re.search(r'state_category\s*=\s*(\S+)', t)
        return tot, (cat.group(1) if cat else '?'), fn
    return None, None, None

for s in bad:
    tot, cat, fn = level_sum(G, s)
    print(f'   s{s:<4} 总等级={tot}  类别={cat}  ← {fn}')
print()

print('  对照（未报错的州，各取10个）:')
import random
ok_states = [s for s in range(1, 751) if s not in bad and s not in range(709, 718) and s not in range(719, 751)]
for s in [1, 5, 10, 50, 100, 150, 177, 179, 200, 300, 400, 450, 550, 600, 700]:
    tot, cat, fn = level_sum(G, s)
    print(f'   s{s:<4} 总等级={tot}  类别={cat}')
print()

print('=' * 70)
print('【F】州类别定义（原版 + 本地覆盖）')
for tag, base in (('原版', V), ('gamma', G), ('beta', B)):
    dc = os.path.join(base, 'common', 'state_category')
    if os.path.isdir(dc):
        fs = glob.glob(os.path.join(dc, '*.txt'))
        print(f'  [{tag}] {len(fs)} 个: {[os.path.basename(x) for x in fs][:10]}')
        if fs:
            t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
            print(f'    示例头 100 字符: {t[:100]!r}')
    else:
        print(f'  [{tag}] 无目录')
print()

print('=' * 70)
print('【G】id 映射资产盘点（tools/*.json + docs）')
for p in sorted(glob.glob(os.path.join(ROOT, 'tools', '*.json'))):
    sz = os.path.getsize(p)
    print(f'   {os.path.basename(p):45s} {sz:>8,}B')
for p in sorted(glob.glob(os.path.join(ROOT, 'docs', '*'))):
    print(f'   docs/{os.path.basename(p)}')

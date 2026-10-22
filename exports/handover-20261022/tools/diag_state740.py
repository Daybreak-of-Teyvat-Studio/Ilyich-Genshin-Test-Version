# -*- coding: utf-8 -*-
"""diag_state740.py —— 重复州号 / 740州内容 / 宫殿坐标解析追踪"""
import os, re, sys, glob, struct, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# ---- 重复州号扫描 ----
ids = collections.defaultdict(list)
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    if m:
        ids[int(m.group(1))].append(os.path.basename(f))
dups = {k: v for k, v in ids.items() if len(v) > 1}
print(f'州文件 {len(glob.glob(os.path.join(G, "history", "states", "*.txt")))} 个, 唯一 id {len(ids)} 个')
print(f'重复 id: {len(dups)}')
for k, v in sorted(dups.items())[:20]:
    print(f'   id={k}: {v}')
missing = [i for i in range(1, 751) if i not in ids]
print(f'缺失 1-750: {missing[:20]}')

# ---- 740 州内容 ----
print()
for f in glob.glob(os.path.join(G, 'history', 'states', '740*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    print(f'--- {os.path.basename(f)} ---')
    print(t[:700])

# ---- definition kind of 740's provinces ----
gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = c[4]
        except ValueError:
            pass
t = open(glob.glob(os.path.join(G, 'history', 'states', '740*.txt'))[0], encoding='utf-8-sig', errors='replace').read()
m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
provs = [int(x) for x in re.findall(r'\d+', m.group(1))]
print(f'740 省列表 kind: {[(p, gk.get(p)) for p in provs[:30]]}')
print(f'740 中有陆地省: {[p for p in provs if gk.get(p) == "land"]}')

# ---- 宫殿坐标解析 ----
raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
W, H = struct.unpack('<ii', raw[18:26])
RB = W * 3
PIX = raw[off:]
colors = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            colors[(int(c[1]), int(c[2]), int(c[3]))] = int(c[0])
        except ValueError:
            pass

def px(x, z):
    i = z * RB + x * 3
    return colors.get((PIX[i + 2], PIX[i + 1], PIX[i]))

# 省→州
p2s = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        for p in re.findall(r'\d+', m2.group(1)):
            p2s.setdefault(int(p), int(m.group(1)))

print()
print('宫殿坐标解析:')
pal = [(1, 'MOT', 3193, 1065), (121, 'LYY', 3082, 790), (256, 'INA', 3607, 594),
       (347, 'SUM', 2871, 805), (500, 'FON', 2721, 1190), (631, 'NAT', 2357, 748),
       (639, 'NDK', 2295, 1073), (704, 'SNE', 2374, 1758)]
for bst, tag, x, z in pal:
    p = px(int(x), int(z))
    k = gk.get(p) if p else None
    # 找最近陆地
    lp, ld = None, None
    for r in range(1, 60):
        done = False
        for dx in range(-r, r + 1):
            for dz in (r, -r):
                for xx, zz in ((x + dx, z + dz), (x + dz, z + dx)):
                    q = px(xx, zz)
                    if q is not None and gk.get(q) == 'land':
                        lp, ld = q, r
                        done = True
                        break
                if done:
                    break
            if done:
                break
        if done:
            break
    print(f'  {tag}_Palace ({x},{z}): 像素省={p}({k}) 州={p2s.get(p)} | 最近陆地: 省={lp} 州={p2s.get(lp)} 距离={ld}')

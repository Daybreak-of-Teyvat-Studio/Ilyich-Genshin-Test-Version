# -*- coding: utf-8 -*-
"""mapgeo2.py —— 验证检查器与引擎一致（陆地跨州=恰好2条）+ 317修复坐标 + 15州深挖"""
import os, re, sys, glob, struct, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
FLIP = False

color2id, id2kind = {}, {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            pid = int(c[0])
        except ValueError:
            continue
        color2id[(int(c[1]), int(c[2]), int(c[3]))] = pid
        id2kind[pid] = c[4]

raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
w, h = struct.unpack('<ii', raw[18:26])
rowbytes = w * 3
pix = raw[off:]

def px(x, z):
    i = z * rowbytes + x * 3
    b, g, r = pix[i], pix[i + 1], pix[i + 2]
    return color2id.get((r, g, b))

prov2state = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        sid = int(m.group(1))
        for pid in re.findall(r'\d+', m2.group(1)):
            prov2state.setdefault(int(pid), sid)

rows = []
for i, l in enumerate(open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace')):
    if not l.strip():
        continue
    c = l.strip().split(';')
    if len(c) < 7:
        continue
    try:
        rows.append((i + 1, int(c[0]), c[1], float(c[2]), float(c[4]), int(c[6])))
    except ValueError:
        pass

# ---- 分类审计 ----
land_cross, sea_cross, no_color = [], [], []
for ln, st, ty, x, z, p7 in rows:
    p = px(int(x), int(z))
    if p is None:
        no_color.append((ln, st, ty, x, z))
        continue
    s = prov2state.get(p)
    if s is not None and s != st:
        if id2kind.get(p) == 'sea':
            sea_cross.append((ln, st, ty, x, z, p, s))
        else:
            land_cross.append((ln, st, ty, x, z, p, s))

print(f'=== 审计分类 ===')
print(f'  无色像素: {len(no_color)}')
print(f'  海像素跨州（引擎容忍/吸附）: {len(sea_cross)}')
print(f'  ★陆地跨州（引擎报错类）: {len(land_cross)}')
for r in land_cross:
    print(f'    L{r[0]} state={r[1]} {r[2]} x={r[3]} z={r[4]} → 省{r[5]}(州{r[6]})')
print()

# ---- 317 修复坐标：州内省的内部像素，找最近的 ----
print('=== 317 修复坐标候选（省内部像素）===')
def interior_pixels(pid, limit=1):
    """扫描该省的像素，返回远离边界的内部点"""
    out = []
    # 全图扫描太慢？4096x2048=8.4M 像素，单次扫描~几秒，可以接受，缓存在首轮
    return out

# 缓存省 → 像素样本（全图扫一次）
prov_pixels = collections.defaultdict(list)
for z in range(0, h, 2):  # 隔行采样
    base = z * rowbytes
    for x in range(0, w, 2):
        i = base + x * 3
        b, g, r = pix[i], pix[i + 1], pix[i + 2]
        p = color2id.get((r, g, b))
        if p is not None and len(prov_pixels[p]) < 400:
            prov_pixels[p].append((x, z))
print(f'  （采样得到 {len(prov_pixels)} 个省的像素点）')

def interior_near(pid, tx, tz):
    """在省 pid 的像素中找离 (tx,tz) 最近、且 8 邻域同色的内部点"""
    best = None
    for (x, z) in prov_pixels.get(pid, []):
        ok = all(px(x + dx, z + dz) == pid for dx in (-1, 0, 1) for dz in (-1, 0, 1)
                 if 0 <= x + dx < w and 0 <= z + dz < h)
        if not ok:
            continue
        d = abs(x - tx) + abs(z - tz)
        if best is None or d < best[0]:
            best = (d, x, z)
    return best

for ln_orig, x0, z0 in ((20325, 1796, 1396), (38658, 1824, 1409)):
    print(f'  L{ln_orig} 原坐标 ({x0},{z0}) 现解析=省{px(x0,z0)}(州{prov2state.get(px(x0,z0))})')
    cands = []
    for pid in (202, 362, 1011, 1028, 2957, 2963, 2966, 2969, 2973, 2978, 2980):
        r = interior_near(pid, x0, z0)
        if r:
            cands.append((r[0], r[1], r[2], pid))
    cands.sort()
    for c in cands[:5]:
        print(f'     候选: 省{c[3]} 内部点 ({c[1]},{c[2]}) 距离={c[0]}')
    print()

# ---- 15 州：陆地跨州 + 重复行 ----
print('=== 15 州行的异常（陆地跨州 / 同坐标重复）===')
bad15 = [76, 82, 223, 246, 269, 284, 311, 500, 560, 564, 569, 584, 587, 590, 607]
lset = {r[0] for r in land_cross}
for st in bad15:
    srows = [r for r in rows if r[1] == st]
    ll = [r for r in srows if r[0] in lset]
    dup = collections.Counter((r[2], r[3], r[4]) for r in srows)
    ndup = sum(v - 1 for v in dup.values() if v > 1)
    print(f'  s{st:<4} 行={len(srows):<4} 陆地跨州={len(ll):<3} 同坐标重复={ndup}')
print('  对照:')
for st in (5, 400, 179, 600, 1, 177):
    srows = [r for r in rows if r[1] == st]
    ll = [r for r in srows if r[0] in lset]
    dup = collections.Counter((r[2], r[3], r[4]) for r in srows)
    ndup = sum(v - 1 for v in dup.values() if v > 1)
    print(f'  s{st:<4} 行={len(srows):<4} 陆地跨州={len(ll):<3} 同坐标重复={ndup}')

# ---- kind 检查几个关键省 ----
print()
print('=== kind 抽查 ===')
for p in (47, 7765, 7481, 7611, 7139, 6687, 2957, 765, 890):
    print(f'   省{p}: kind={id2kind.get(p)} 属州={prov2state.get(p)}')

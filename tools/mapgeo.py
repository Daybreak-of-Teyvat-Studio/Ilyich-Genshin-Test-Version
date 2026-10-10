# -*- coding: utf-8 -*-
"""mapgeo.py —— provinces.bmp 坐标检查器：
1) 确定坐标映射约定（用已知 col7 的行反推）
2) 全量审计 40876 行 buildings：坐标所在省/州 vs 第1列州
3) 为两行坏行找 317 州内的最近修复坐标
4) 15 个 too many 州的行异常扫描（跨州/重复）
"""
import os, re, sys, glob, struct, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# ---- 读 definition ----
color2id = {}
id2kind = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            pid = int(c[0])
        except ValueError:
            continue
        color2id[(int(c[1]), int(c[2]), int(c[3]))] = pid
        id2kind[pid] = c[4]
print(f'definition: {len(color2id)} 色 / {len(id2kind)} 省')

# ---- 读 provinces.bmp（24bit, bottom-up）----
raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
w, h = struct.unpack('<ii', raw[18:26])
bpp = struct.unpack('<H', raw[28:30])[0]
comp = struct.unpack('<I', raw[30:34])[0]
print(f'bmp: {w}x{h} bpp={bpp} comp={comp} offset={off} size={len(raw)}')
assert bpp == 24 and comp == 0
rowbytes = w * 3
pix = raw[off:]

def px(x, z, flip):
    """flip=False: 直读(顶行在前) ; flip=True: bottom-up"""
    py = (h - 1 - z) if flip else z
    i = py * rowbytes + x * 3
    b, g, r = pix[i], pix[i + 1], pix[i + 2]
    return color2id.get((r, g, b))

# ---- 省→州 ----
prov2state = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'id\s*=\s*(\d+)', t)
    if not m:
        continue
    sid = int(m.group(1))
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m2:
        for pid in re.findall(r'\d+', m2.group(1)):
            prov2state.setdefault(int(pid), sid)
print(f'州文件: {len(set(prov2state.values()))} 州 / 省→州 {len(prov2state)} 条')

# ---- 读 buildings ----
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
print(f'buildings: {len(rows)} 行')

# ---- 确定 flip 约定：用 col7!=0 且 col7 是海省的 naval/浮动港行 ----
print()
print('=== flip 判定（col7!=0 的行）===')
tests = [r for r in rows if r[5] != 0]
ok_false = ok_true = 0
for ln, st, ty, x, z, p7 in tests[:400]:
    for flip, cnt in ((False, 'F'), (True, 'T')):
        pass
    a = px(int(x), int(z), False)
    b = px(int(x), int(z), True)
    is_sea = id2kind.get(p7) == 'sea'
    if a == p7:
        ok_false += 1
    if b == p7:
        ok_true += 1
print(f'  共 {len(tests)} 行 col7!=0（取前400测试）: 直读命中={ok_false} / 翻转命中={ok_true}')

# 用 317 的 naval_base_spawn 行直接看
print('  317 naval 行 (1789.5,1389.5) col7=7611:')
print(f'    直读 -> {px(1789, 1389, False)}   翻转 -> {px(1789, 1389, True)}')
print(f'    直读2 -> {px(1816, 1403, False)}   翻转2 -> {px(1816, 1403, True)}')

# ---- 全量审计（两种 flip 各跑一遍，选 mismatch 少的）----
print()
print('=== 全量审计 ===')
for flip in (False, True):
    bad = []
    for ln, st, ty, x, z, p7 in rows:
        p = px(int(x), int(z), flip)
        if p is None:
            bad.append((ln, st, ty, x, z, p7, '无色'))
            continue
        s = prov2state.get(p)
        if s is not None and s != st:
            bad.append((ln, st, ty, x, z, p7, f'实为州{s}省{p}'))
    print(f'  flip={flip}: 不匹配 {len(bad)} 行')
    for b in bad[:12]:
        print(f'    L{b[0]} state={b[1]} {b[2]} x={b[3]} z={b[4]} col7={b[5]} → {b[6]}')
    if len(bad) < 200:
        globals()['AUDIT'] = bad
        globals()['FLIP'] = flip
        break

# ---- 两行坏行的修复坐标搜索 ----
print()
print('=== 坏行修复坐标搜索（目标：落在 317 州的省）===')
for ln_orig, x0, z0 in ((20325, 1796, 1396), (38658, 1824, 1409)):
    found = None
    for r in range(0, 60):
        for dx in range(-r, r + 1):
            for dz in (-r, r) if r else (0,):
                pass
        # 简化：按半径环搜索最近
        cand = []
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if max(abs(dx), abs(dz)) != r:
                    continue
                x, z = x0 + dx, z0 + dz
                p = px(x, z, FLIP)
                if p is not None and prov2state.get(p) == 317:
                    cand.append((abs(dx) + abs(dz), x, z, p))
        if cand:
            cand.sort()
            found = cand[0]
            break
    print(f'  L{ln_orig} ({x0},{z0}) → 最近 317 坐标: {found}')

# ---- 15 州的行：跨州 + 重复 ----
print()
print('=== 15 州的行异常扫描 ===')
bad15 = [76, 82, 223, 246, 269, 284, 311, 500, 560, 564, 569, 584, 587, 590, 607]
for st in bad15:
    srows = [r for r in rows if r[1] == st]
    cross = []
    for ln, st2, ty, x, z, p7 in srows:
        p = px(int(x), int(z), FLIP)
        s = prov2state.get(p)
        if s is not None and s != st:
            cross.append((ln, ty, x, z, s))
    dup = collections.Counter((r[2], r[3], r[4]) for r in srows)
    ndup = sum(v - 1 for v in dup.values() if v > 1)
    print(f'  s{st:<4} 行数={len(srows):<4} 跨州={len(cross):<3} 同坐标重复={ndup}')
    for c in cross[:3]:
        print(f'      L{c[0]} {c[1]} ({c[2]},{c[3]}) 实为州{c[4]}')
print()
print('  对照组:')
for st in (5, 400, 179, 600, 1):
    srows = [r for r in rows if r[1] == st]
    cross = []
    for ln, st2, ty, x, z, p7 in srows:
        p = px(int(x), int(z), FLIP)
        s = prov2state.get(p)
        if s is not None and s != st:
            cross.append((ln, ty, x, z, s))
    dup = collections.Counter((r[2], r[3], r[4]) for r in srows)
    ndup = sum(v - 1 for v in dup.values() if v > 1)
    print(f'  s{st:<4} 行数={len(srows):<4} 跨州={len(cross):<3} 同坐标重复={ndup}')

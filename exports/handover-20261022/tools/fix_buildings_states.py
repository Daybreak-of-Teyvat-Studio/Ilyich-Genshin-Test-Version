# -*- coding: utf-8 -*-
"""
map/buildings.txt 正确同步（第三版，含边界点精确修正）。

踩过的坑：
  · 只改 history/states/*.txt 而漏掉 buildings.txt → 游戏忽略建筑，
    沿海省变成"coastal but has no port"并崩溃
  · 把所有条目都改成新州 → 原州丢失「州级生成点」，
    游戏报 no air base site / no rocket site / no gun emplacement 并崩溃

正确规则：
  · 坐标反查省：像素 = (x, 2048 - z)，用 positions.txt 验证 8021/8021
  · 州级生成点（每州数量恒定的类型）→ 留在原州，把位置挪到原州内最近的省
  · 其余（港口/要塞/工厂/补给站等随省走的）→ 声明州改为新州
  · 岸边 1px 的残留条目（游戏按自己的解析判它在省界内）→ 按「类型 + 原州 + 离该省最近」精确挑出

  python fix_buildings_states.py [--dry]
"""
import os, re, sys, shutil, datetime, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
DRY = '--dry' in sys.argv

# 我们转移过的省: 省 -> (原州, 新州)
MOVED = {918: (437, 416), 2354: (437, 416), 3310: (416, 421), 2294: (412, 404),
         3254: (400, 404), 3242: (404, 392), 782: (390, 28), 2394: (28, 381),
         2051: (382, 28), 3197: (382, 28), 1170: (411, 400), 3279: (401, 408),
         3263: (398, 410), 1656: (418, 408), 3314: (419, 410), 2127: (419, 420)}
# 州级生成点（每州数量恒定；由数据判定，见 .scratch/levels.py）
STATE_LEVEL = {'air_base', 'fuel_silo', 'radar_station', 'nuclear_reactor_spawn',
               'rocket_site_spawn', 'synthetic_refinery', 'stronghold_network',
               'anti_air_building'}
# 游戏上一次报的残留错配 (省, 类型) —— 按最近距离精确挑条目
EDGE_WANT = [(1170, 'coastal_bunker'), (1170, 'naval_supply_hub'),
             (1656, 'naval_headquarters')]

# ---------------- 几何 ----------------
rgb2id, kind = {}, {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
        kind[int(a[0])] = a[4]
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)

p2s, s2p = {}, collections.defaultdict(list)
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for p in re.findall(r'\d+', re.search(r'provinces = \{([^}]*)\}', t).group(1)):
        p2s[int(p)] = sid
        s2p[sid].append(int(p))
for p, (old, new) in MOVED.items():
    assert p2s.get(p) == new, f'省 {p} 现值 {p2s.get(p)} != {new}'

ptxt = open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig',
            errors='replace').read()
POS = {}
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)', ptxt):
    POS[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
print(f'省 {len(p2s)} / 州 {len(s2p)} / positions {len(POS)}')


def prov_at(x, z, rad=1):
    xi, yi = int(round(x)), int(round(H - z))
    if 0 <= xi < W and 0 <= yi < H:
        p = int(prov[yi, xi])
        if p and kind.get(p) == 'land':
            return p
    for d in range(1, rad + 1):
        for dy in range(-d, d + 1):
            for dx in range(-d, d + 1):
                if max(abs(dx), abs(dy)) != d:
                    continue
                yy, xx = yi + dy, xi + dx
                if 0 <= xx < W and 0 <= yy < H:
                    q = int(prov[yy, xx])
                    if q and kind.get(q) == 'land':
                        return q
    return 0


def nearest_in(state, p):
    px, _, pz = POS.get(p, (2048, 0, 1024))
    c = [q for q in s2p[state] if q in POS and q != p]
    c.sort(key=lambda q: (POS[q][0] - px) ** 2 + (POS[q][2] - pz) ** 2)
    return c


raw = open(BP, 'rb').read()
assert raw[:3] != b'\xef\xbb\xbf', 'buildings.txt 带 BOM'
lines = raw.decode('utf-8').split('\r\n')
before = collections.defaultdict(collections.Counter)
for l in lines:
    if l.strip():
        f = l.split(';')
        before[f[1]][int(f[0])] += 1

# ---------------- 主修正 ----------------
used = collections.defaultdict(collections.Counter)
relocate, reown, skipped = [], [], []
for i, l in enumerate(lines):
    if not l.strip():
        continue
    f = l.split(';')
    st, bt, x, z = int(f[0]), f[1], float(f[2]), float(f[4])
    p = prov_at(x, z, 1)
    if p not in MOVED:
        continue
    old, new = MOVED[p]
    if st != old:
        skipped.append((i + 1, p, st, bt))
        continue
    if bt in STATE_LEVEL:
        cands = nearest_in(old, p)
        if not cands:
            relocate.append((i + 1, p, bt, None))
            continue
        q = cands[used[(old, bt)][p] % len(cands)]
        used[(old, bt)][p] += 1
        qx, qy, qz = POS[q]
        f[2], f[3], f[4] = f'{qx:.2f}', f'{qy:.2f}', f'{qz:.2f}'
        relocate.append((i + 1, p, bt, q))
    else:
        f[0] = str(new)
        reown.append((i + 1, p, old, new, bt))
    lines[i] = ';'.join(f)
print(f'\n州级生成点留在原州（挪位置）: {len(relocate)} 条')
print(f'随省走（改州）: {len(reown)} 条')
print(f'声明州已非原州、跳过: {len(skipped)} 条 {skipped[:4]}')

# ---------------- 岸边 1px 残留（按游戏报告精确挑） ----------------
fixed_edge = []
for P, bt in EDGE_WANT:
    old, new = MOVED[P]
    yy, xx = np.nonzero(prov == P)
    if not len(yy):
        print(f'  !! 省 {P} 无像素'); continue
    xs_, ys_ = xx.astype(float), yy.astype(float)
    best = None
    for i, l in enumerate(lines):
        if not l.strip():
            continue
        f = l.split(';')
        if f[1] != bt or int(f[0]) != old:
            continue
        d = float(np.min(np.hypot(xs_ - float(f[2]), ys_ - (H - float(f[4])))))
        if best is None or d < best[0]:
            best = (d, i, f)
    if best is None:
        print(f'  !! 省 {P} 找不到类型 {bt} 且声明 {old} 的条目'); continue
    d, i, f = best
    if d > 2.5:
        print(f'  !! 省 {P} {bt} 最近条目也有 {d:.1f}px，暂时放弃'); continue
    f[0] = str(new)
    lines[i] = ';'.join(f)
    fixed_edge.append((i + 1, P, bt, d))
    print(f'  岸边修正: 行 {i+1} 省 {P} {bt} 距 {d:.1f}px  州 {old} -> {new}')

# ---------------- 写盘 ----------------
out = '\r\n'.join(lines)
if not DRY:
    bdir = os.path.join(ROOT, '.backups',
                        'map_buildings_v3_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(bdir, exist_ok=True)
    shutil.copy2(BP, os.path.join(bdir, 'buildings.txt'))
    with open(BP, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)
    print(f'\n已写入 {BP}\n备份 {bdir}')
else:
    print('\n[DRY] 未写盘')

# ---------------- 复核 ----------------
t2 = (open(BP, 'rb').read().decode('utf-8') if not DRY else out)
l2 = t2.split('\r\n')
after = collections.defaultdict(collections.Counter)
for l in l2:
    if l.strip():
        f = l.split(';')
        after[f[1]][int(f[0])] += 1
print(f'复核: 行数 {len(l2)}（原 {len(lines)}）; CRLF {t2.count(chr(13) + chr(10))}; '
      f'无BOM {t2[:1] != chr(0xef)}')
bad = []
for bt in sorted(STATE_LEVEL):
    diff = {k: (before[bt].get(k, 0), after[bt].get(k, 0))
            for k in set(before[bt]) | set(after[bt])
            if before[bt].get(k, 0) != after[bt].get(k, 0)}
    if diff:
        bad.append((bt, list(diff.items())[:5]))
print(f'复核: 州级类型每州数量与原始一致? {"是 ✓" if not bad else "否"}')
for x in bad:
    print('   !', x)
miss = [s for s in s2p if any(after[bt].get(s, 0) == 0 for bt in STATE_LEVEL)]
print(f'复核: 缺州级生成点的州: {len(miss)} 个 {sorted(miss)[:15]}')
still = []
for i, l in enumerate(l2, 1):
    if not l.strip():
        continue
    f = l.split(';')
    p = prov_at(float(f[2]), float(f[4]), 1)
    if p and p in MOVED and int(f[0]) != MOVED[p][1] and f[1] not in STATE_LEVEL:
        still.append((i, p, f[0], f[1]))
print(f'复核: 随省走但仍不符: {len(still)} 条 {still[:6]}')

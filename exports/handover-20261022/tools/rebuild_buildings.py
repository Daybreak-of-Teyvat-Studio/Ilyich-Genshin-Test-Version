# -*- coding: utf-8 -*-
"""
按当前 history/states 重建 map/buildings.txt 的州列（不依赖任何历史/移动清单）。

规则（与之前确认的一致）：
  · 省由坐标反查：像素 = (x, 地图高度 - z)，Z 轴向上、位图 Y 向下
  · 先用 3×3 邻域候选：若候选里有任一省的**当前州**等于声明州 → 该条目本来就对，不动
    （这样能避开坐标抖动导致的误改）
  · 否则取出"实际所在省"：
      - 随省走的类型 → 声明州改成实际州
      - 州级生成点类型 → 留在声明州，把坐标挪到该州内最近的省（依次轮换，避免堆叠）
  · 改前备份；改后核对：州级类型每州数量必须与原始一致、无州缺生成点

  python rebuild_buildings.py [--dry]
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
ORIG = os.path.join(ROOT, '.backups', 'map_buildings_20260923_222654', 'buildings.txt')
DRY = '--dry' in sys.argv

STATE_LEVEL = {'air_base', 'fuel_silo', 'radar_station', 'nuclear_reactor_spawn',
               'rocket_site_spawn', 'synthetic_refinery', 'stronghold_network',
               'anti_air_building'}

# ---- 几何 ----
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
klut = np.zeros(len(uniq), np.uint8)
for i, k in enumerate(uniq):
    k = int(k)
    pid = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
    plut[i] = pid
    klut[i] = 1 if kind.get(pid, 'land') == 'land' else 0
prov = plut[inv].reshape(H, W)
landpx = klut[inv].reshape(H, W).astype(bool)

p2s, s2p = {}, collections.defaultdict(list)
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for p in re.findall(r'\d+', re.search(r'provinces = \{([^}]*)\}', t).group(1)):
        p2s[int(p)] = sid
        s2p[sid].append(int(p))
print(f'省 {len(p2s)} / 州 {len(s2p)}')

ptxt = open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig',
            errors='replace').read()
POS = {}
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)', ptxt):
    POS[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))


def cands_near(x, z, r=1):
    """3x3(或更大) 邻域内的陆地省，按距离排序"""
    xi, yi = int(round(x)), int(round(H - z))
    out = {}
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            xx, yy = xi + dx, yi + dy
            if 0 <= xx < W and 0 <= yy < H and landpx[yy, xx]:
                p = int(prov[yy, xx])
                if p:
                    d = dx * dx + dy * dy
                    if p not in out or d < out[p]:
                        out[p] = d
    return sorted(out, key=lambda p: out[p])


def nearest_in(state, x, z):
    cx, cz = x, H - z
    c = [q for q in s2p[state] if q in POS]      # 单省州也能返回，否则搬不动
    c.sort(key=lambda q: (POS[q][0] - cx) ** 2 + (POS[q][2] - (H - z)) ** 2)
    return c


raw = open(BP, 'rb').read()
assert raw[:3] != b'\xef\xbb\xbf'
lines = raw.decode('utf-8').split('\r\n')
print(f'buildings.txt {len(lines)} 行（{len(raw)} 字节）')

before = collections.defaultdict(collections.Counter)
for l in lines:
    if l.strip():
        f = l.split(';')
        if len(f) == 7:
            before[f[1]][int(f[0])] += 1

ok_untouched = reown = reloc = nofix = 0
used = collections.defaultdict(collections.Counter)
for i, l in enumerate(lines):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    st, bt, x, z = int(f[0]), f[1], float(f[2]), float(f[4])
    cs = cands_near(x, z, 1)
    if not cs:
        nofix += 1
        continue
    if any(p2s.get(p) == st for p in cs):
        ok_untouched += 1                     # 邻域里有属于声明州的省 → 本来就对
        continue
    home = cs[0]
    if bt in STATE_LEVEL:
        c2 = nearest_in(st, x, z)
        if not c2:
            nofix += 1
            continue
        q = c2[used[(st, bt)][int(x) * 100003 + int(z)] % len(c2)]
        used[(st, bt)][int(x) * 100003 + int(z)] += 1
        qx, qy, qz = POS[q]
        f[2], f[3], f[4] = f'{qx:.2f}', f'{qy:.2f}', f'{qz:.2f}'
        reloc += 1
    else:
        f[0] = str(p2s[home])
        reown += 1
    lines[i] = ';'.join(f)

print(f'\n保持不变（邻域内有本州省）: {ok_untouched}')
print(f'随省改州: {reown}')
print(f'州级生成点就地挪位置: {reloc}')
print(f'无法判定、跳过: {nofix}')

out = '\r\n'.join(lines)
if not DRY:
    bdir = os.path.join(ROOT, '.backups',
                        'map_buildings_rebuild_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(bdir, exist_ok=True)
    shutil.copy2(BP, os.path.join(bdir, 'buildings.txt'))
    with open(BP, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)
    print(f'\n已写入，备份 {bdir}')
else:
    print('\n[DRY] 未写盘')

# ---- 复核 ----
t2 = (open(BP, 'rb').read().decode('utf-8') if not DRY else out)
l2 = t2.split('\r\n')
after = collections.defaultdict(collections.Counter)
for l in l2:
    if l.strip():
        f = l.split(';')
        if len(f) == 7:
            after[f[1]][int(f[0])] += 1
print(f'复核: 行数 {len(l2)}（原 {len(lines)}）; CRLF {t2.count(chr(13)+chr(10))}; '
      f'无BOM {t2[:1] != chr(0xef)}')

if os.path.exists(ORIG):
    ob = collections.defaultdict(collections.Counter)
    for l in open(ORIG, encoding='utf-8-sig', newline='').read().split('\r\n'):
        if l.strip():
            f = l.split(';')
            if len(f) == 7:
                ob[f[1]][int(f[0])] += 1
    bad = 0
    for bt in sorted(STATE_LEVEL):
        diff = {k for k in set(ob[bt]) | set(after[bt]) if ob[bt].get(k, 0) != after[bt].get(k, 0)}
        if diff:
            bad += len(diff)
            print(f'  ! {bt}: {len(diff)} 个州数量不符 {list(diff)[:6]}')
    miss = [s for s in s2p if any(after[bt].get(s, 0) == 0 for bt in STATE_LEVEL)]
    print(f'复核: 州级类型每州数量与原始一致? {"是 ✓" if bad == 0 else "否"}')
    print(f'复核: 缺州级生成点的州 {len(miss)} 个 {sorted(miss)[:10]}')
    for bt in sorted(set(ob) | set(after), key=lambda x: -sum(ob[x].values())):
        o, n = sum(ob[bt].values()), sum(after[bt].values())
        if o != n:
            print(f'  ! 总数变化 {bt}: {o} -> {n}')
# 模拟游戏校验：逐条查 省->州 是否与声明一致
mism = 0
for l in l2:
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    cs = cands_near(float(f[2]), float(f[4]), 1)
    if cs and not any(p2s.get(p) == int(f[0]) for p in cs):
        mism += 1
print(f'复核: 声明州与坐标不符（按 3×3 判定）: {mism} 条')



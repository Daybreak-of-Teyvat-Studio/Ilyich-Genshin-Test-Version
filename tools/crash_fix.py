# -*- coding: utf-8 -*-
"""
崩溃修复脚本（09-27 海州引入的 bug）：
  A. buildings.txt：所有条目按「标记点吸附最近陆地省」定州（水面标记不再归海州）
  B. 41 个海州：state_category = ocean → wasteland
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

kind = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
rgb2id = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)
prov_land = np.isin(prov, [p for p, k in kind.items() if k == 'land'])

p2s = {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for p in re.findall(r'\d+', re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1)):
        p2s[int(p)] = sid

_snap_cache = {}


def snap_land(y, x, maxr=15):
    keyc = (y, x)
    if keyc in _snap_cache:
        return _snap_cache[keyc]
    res = (None, -1)
    if 0 <= y < H and 0 <= x < W and prov_land[y, x]:
        res = (int(prov[y, x]), 0)
    else:
        for r in range(1, maxr + 1):
            y0, y1 = max(0, y - r), min(H, y + r + 1)
            x0, x1 = max(0, x - r), min(W, x + r + 1)
            subl = prov_land[y0:y1, x0:x1]
            if subl.any():
                vals = prov[y0:y1, x0:x1][subl]
                res = (int(collections.Counter(vals.tolist()).most_common(1)[0][0]), r)
                break
    _snap_cache[keyc] = res
    return res


raw = open(BP, 'rb').read()
lines = raw.decode('utf-8').split('\r\n')

stats = collections.Counter()
dist = collections.Counter()
type_water = collections.Counter()
for l in lines:
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    x, z = float(f[2]), float(f[4])
    y, xx = int(round(H - z)), int(round(x))
    if not (0 <= y < H and 0 <= xx < W):
        stats['越界'] += 1
        continue
    p = int(prov[y, xx])
    if kind.get(p) == 'land':
        stats['陆地直接命中'] += 1
    else:
        type_water[f[1]] += 1
        lp, r = snap_land(y, xx)
        stats['水面吸附' if lp else '水面无法吸附'] += 1
        if lp:
            dist[r] += 1
print('=== 扫描统计 ===')
print(' ', dict(stats))
print('  吸附半径分布:', dict(sorted(dist.items())))
print('  水面标记按类型:', dict(type_water.most_common()))

# 应用：州列 = 吸附陆省的州
changed = 0
for i, l in enumerate(lines):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    x, z = float(f[2]), float(f[4])
    y, xx = int(round(H - z)), int(round(x))
    if not (0 <= y < H and 0 <= xx < W):
        continue
    lp, r = snap_land(y, xx)
    if lp is None:
        continue
    want = p2s.get(lp)
    if want is None:
        continue
    if int(f[0]) != want:
        f[0] = str(want)
        lines[i] = ';'.join(f)
        changed += 1
print(f'\n=== A. buildings.txt 改州列：{changed} 条 ===')

bdir = os.path.join(ROOT, '.backups', 'crashfix_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(BP, os.path.join(bdir, 'buildings.txt.orig'))
open(BP, 'w', encoding='utf-8', newline='').write('\r\n'.join(lines))

# B. 海州 state_category
print('\n=== B. 海州 state_category ocean → wasteland ===')
n = 0
for sid in range(862, 903):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    if not os.path.exists(fp):
        continue
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = open(fp, encoding='utf-8-sig', newline='').read()
    t2 = t.replace('state_category = ocean', 'state_category = wasteland')
    if t2 != t:
        with open(fp, 'w', encoding='utf-8', newline='') as fh:
            fh.write(t2)
        n += 1
print(f'  已改 {n} 个海州文件')

# C. 复验
print('\n=== C. 复验 ===')
mism = 0
for l in open(BP, encoding='utf-8-sig', newline='').read().split('\r\n'):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    x, z = float(f[2]), float(f[4])
    y, xx = int(round(H - z)), int(round(x))
    if not (0 <= y < H and 0 <= xx < W):
        continue
    lp, r = snap_land(y, xx)
    if lp and p2s.get(lp) != int(f[0]):
        mism += 1
print(f'  buildings 声明州与「吸附陆省所属州」不符: {mism}（应 0）')

# 36 个崩溃警告省是否恢复港口
WARN = [3, 492, 758, 914, 1458, 1772, 1923, 2226, 2267, 2477, 2570, 2602, 2612, 2655, 2831, 2849,
        2884, 3032, 3148, 3172, 3178, 3251, 3480, 3566, 3600, 3613, 3650, 3654, 3765, 3947, 4498,
        4595, 4619, 4678, 4689, 4698]
have = set()
for l in open(BP, encoding='utf-8-sig', newline='').read().split('\r\n'):
    f = l.split(';')
    if len(f) == 7 and f[1] == 'naval_base_spawn':
        x, z = float(f[2]), float(f[4])
        lp, r = snap_land(int(round(H - z)), int(round(x)))
        if lp:
            have.add(lp)
lost = [p for p in WARN if p not in have]
print(f'  36 个警告省里仍无港口位: {len(lost)} {lost}')
print(f'  naval_base_spawn 总数: {sum(1 for l in open(BP, encoding="utf-8-sig", newline="").read().split(chr(13)+chr(10)) if l.split(";")[1:2] == ["naval_base_spawn"])}')
print(f'\n  备份: {bdir}')

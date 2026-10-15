# -*- coding: utf-8 -*-
"""rebuild_buildings_final 的 DRY 诊断版：只统计不改文件"""
import os, re, sys, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\rbf_dry_out.txt'
SL = {'air_base': 1, 'fuel_silo': 1, 'radar_station': 1, 'nuclear_reactor_spawn': 1,
      'rocket_site_spawn': 1, 'synthetic_refinery': 1, 'stronghold_network': 1,
      'anti_air_building': 3}
NAVAL = {'naval_base_spawn', 'naval_headquarters', 'naval_supply_hub',
         'coastal_bunker', 'floating_harbor'}
o = []

s2p, s2o = {}, {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    s2o[sid] = mo.group(1) if mo else None
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}

kind = {}
rgb2id = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
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
lmask = np.isin(prov, [q for q, k in kind.items() if k == 'land'])
_cache = {}

def snap(y, x):
    if (y, x) in _cache:
        return _cache[(y, x)]
    r = None
    if 0 <= y < H and 0 <= x < W and lmask[y, x]:
        r = int(prov[y, x])
    else:
        for rr in range(1, 16):
            y0, y1 = max(0, y - rr), min(H, y + rr + 1)
            x0, x1 = max(0, x - rr), min(W, x + rr + 1)
            sl = lmask[y0:y1, x0:x1]
            if sl.any():
                vals = prov[y0:y1, x0:x1][sl]
                r = int(collections.Counter(vals.tolist()).most_common(1)[0][0])
                break
    _cache[(y, x)] = r
    return r

def game_state(f):
    if f[1] in NAVAL:
        p7 = int(f[6]) if f[6].isdigit() else 0
        if p7 and kind.get(p7) == 'land':
            return p2s.get(p7)
    y, x = int(round(H - float(f[4]))), int(round(float(f[2])))
    if not (0 <= y < H and 0 <= x < W):
        return None
    lp = snap(y, x)
    return p2s.get(lp) if lp else None

raw = open(BP, 'rb').read()
nl = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl)
shifts = collections.Counter()
total = 0
bad7 = 0
cur = collections.defaultdict(lambda: collections.defaultdict(int))
for l in lines:
    f = l.split(';')
    if len(f) != 7:
        bad7 += 1
        continue
    total += 1
    want = game_state(f)
    if want is None:
        if f[1] in SL:
            shifts['SL_删除(无地)'] += 1
        continue
    if int(f[0]) != want:
        shifts['改州'] += 1
        shifts[f'{f[0]}→{want}'] += 1
    if f[1] in SL:
        cur[f[1]][int(f[0])] += 1
        if s2o.get(int(f[0])) is None:
            shifts['海州SL删'] += 1
        elif cur[f[1]][int(f[0])] > SL[f[1]]:
            shifts['超配SL删'] += 1

appends = collections.Counter()
for st in sorted(s2p):
    if s2o.get(st) is None:
        continue
    land = [q for q in s2p[st] if q in {} or True]  # 仅计数用
    if not land:
        continue
    for bt, want_n in SL.items():
        have = cur[bt].get(st, 0)
        if want_n - have > 0:
            appends[bt] += want_n - have

o.append(f'总行数 {total}（7 字段），非 7 字段行 {bad7}')
o.append('')
o.append('===== 需要调整的统计 =====')
for k, v in shifts.most_common(60):
    o.append(f'  {k}: {v}')
o.append('')
o.append('===== SL 需要补缺（按类型） =====')
for k, v in appends.items():
    o.append(f'  {k}: +{v}')
o.append(f'  合计 +{sum(appends.values())}')
o.append('')
o.append('===== 重点州现状（当前 col1 计数） =====')
cur_all = collections.Counter()
for l in lines:
    f = l.split(';')
    if len(f) == 7 and f[0].isdigit():
        cur_all[int(f[0])] += 1
for s in (62, 63, 65, 66, 67, 89, 90, 94):
    o.append(f'  s{s}: 现 {cur_all.get(s,0)} 行')

open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

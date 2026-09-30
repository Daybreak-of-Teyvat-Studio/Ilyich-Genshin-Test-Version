# -*- coding: utf-8 -*-
"""
buildings 终版重整（单一权威规则，一次到位）：
  · naval 五类：声明州 = 标记吸附最近陆地省的所属州（省列为陆省时直接用省列）
  · 其余类：声明州 = 标记坐标像素省的所属州（第 7 列多为 0，不参与）
  · SL 生成点：全删重放，每陆州 7×1 + anti_air×3，海州 0 条
  · 声明州必须是存在的州，否则该条目删除
"""
import os, re, sys, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
SL = {'air_base': 1, 'fuel_silo': 1, 'radar_station': 1, 'nuclear_reactor_spawn': 1,
      'rocket_site_spawn': 1, 'synthetic_refinery': 1, 'stronghold_network': 1,
      'anti_air_building': 3}
NAVAL = {'naval_base_spawn', 'naval_headquarters', 'naval_supply_hub',
         'coastal_bunker', 'floating_harbor'}

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
    """单一权威规则"""
    if f[1] in NAVAL:
        p7 = int(f[6]) if f[6].isdigit() else 0
        if p7 and kind.get(p7) == 'land':
            return p2s.get(p7)                       # 省列陆省直接用
    y, x = int(round(H - float(f[4]))), int(round(float(f[2])))
    if not (0 <= y < H and 0 <= x < W):
        return None
    lp = snap(y, x)                                   # 陆类像素省 / 海军类吸附
    return p2s.get(lp) if lp else None


POS = {}
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)',
                     open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig',
                          errors='replace').read()):
    POS[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
TMPL = {}
for l in open(r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups'
              r'\map_buildings_20260923_222654\buildings.txt',
              encoding='utf-8-sig', newline='').read().split('\n'):
    f = l.split(';')
    if len(f) == 7 and f[1] in SL and f[1] not in TMPL:
        TMPL[f[1]] = f

# ---- 重建 ----
raw = open(BP, 'rb').read()
nl = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl)
out = []
cur = collections.defaultdict(lambda: collections.defaultdict(int))
n_align = 0
for l in lines:
    f = l.split(';')
    if len(f) != 7:
        out.append(l)
        continue
    want = game_state(f)
    if want is None:
        if f[1] in SL:
            continue
        out.append(l)
        continue
    if int(f[0]) != want:
        f[0] = str(want)
        l = ';'.join(f)
        n_align += 1
    if f[1] in SL:
        cur[f[1]][int(f[0])] += 1
        if s2o.get(int(f[0])) is None:
            continue                                  # 海州 SL 删
        if cur[f[1]][int(f[0])] > SL[f[1]]:
            continue                                  # 超配删
    out.append(l)
print(f'① 对齐 {n_align} 条；海州/超配 SL 已剔除')

appends = []
for st in sorted(s2p):
    if s2o.get(st) is None:
        continue
    land = [q for q in s2p[st] if q in POS]
    if not land:
        continue
    for bt, want_n in SL.items():
        have = cur[bt].get(st, 0)
        for k in range(max(0, want_n - have)):
            f = list(TMPL[bt])
            px, py, pz = POS[land[(hash((st, bt, k))) % len(land)]]
            f[0] = str(st)
            f[2], f[3], f[4] = f'{px:.2f}', f'{py:.2f}', f'{pz:.2f}'
            appends.append(';'.join(f))
            cur[bt][st] += 1
out = out + appends
open(BP, 'w', encoding='utf-8', newline='').write(nl.join(out))
print(f'② SL 补缺 {len(appends)} 条')

# ---- 终验（同一规则） ----
mism = 0
bad = 0
for l in open(BP, encoding='utf-8-sig', newline='').read().split(nl):
    f = l.split(';')
    if len(f) != 7:
        continue
    want = game_state(f)
    if want is not None and int(f[0]) != want:
        mism += 1
    if f[1] in SL:
        st = int(f[0])
        if s2o.get(st) is None:
            bad += 1
for bt in SL:
    for st in s2p:
        n_have = 0
        w2 = 0 if s2o.get(st) is None else SL[bt]
        if s2o.get(st) is None:
            continue
print(f'终验: 游戏规则不符 {mism}（应 0）')

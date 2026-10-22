# -*- coding: utf-8 -*-
"""
地形改造（三步顺序覆盖版）：
  步骤1：全部陆地省 → plains（水域省保持）
  步骤2：DRA/CYG→mountain，MHL→hills，SGD/SDH/SGS→desert
  步骤3：所有陆地省（六国不豁免）按地理特征重设：
         城市(spawn_city)→urban > 沿海→plains > 原版山脉→mountain
         > 原版森林→forest > 邻山且海拔抬升→hills > 其余 plains
落地：definition.csv（机制）+ terrain.bmp（视觉，每省像素设为新地形 index）。
"""
import os, re, sys, shutil, datetime, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
VAN = r'F:\Steam\steamapps\common\Hearts of Iron IV'
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DRY = '--dry' in sys.argv

# ---- 原版 index→type ----
vt = open(os.path.join(VAN, 'common', 'terrain', '00_terrain.txt'), encoding='utf-8-sig',
          errors='replace').read()
i = vt.find('terrain = {')
blk = vt[i: vt.find('}', vt.find('spawn_city') + 200) + 1]
IDX2TYPE, SPAWN = {}, []
for m in re.finditer(r'=\s*\{\s*type = (\w+)\s+color = \{\s*(\d+)\s*\}(.*?)\}', blk, re.S):
    idx, typ, rest = int(m.group(2)), m.group(1), m.group(3)
    IDX2TYPE[idx] = typ
    if 'spawn_city' in rest:
        SPAWN.append(idx)
print('index→type:', {k: v for k, v in sorted(IDX2TYPE.items())})
print('spawn_city index:', SPAWN)
TYPE2IDX = {'plains': 5, 'forest': 1, 'hills': 2, 'desert': 3, 'mountain': 6,
            'urban': 13, 'marsh': 9, 'jungle': 21}

# ---- definition.csv ----
DEF = os.path.join(G, 'map', 'definition.csv')
lines = raw.decode('utf-8').split('\r\n') if False else open(DEF, encoding='utf-8-sig',
             newline='').read().split('\r\n')
rows, kind = [], {}
for li, l in enumerate(lines):
    a = l.split(';')
    if len(a) >= 8 and a[0].strip().isdigit():
        rows.append((li, a))
        kind[int(a[0])] = a[4]
land_ids = {p for p, k in kind.items() if k == 'land'}

# ---- 州/owner ----
s2p, s2o = {}, {}
for f in os.listdir(os.path.join(G, 'history', 'states')):
    t2 = open(os.path.join(G, 'history', 'states', f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t2).group(1))
    s2o[sid] = re.search(r'\bowner\s*=\s*(\w+)', t2).group(1)
    s2p[sid] = [int(x) for x in re.search(r'provinces = \{([^}]*)\}', t2).group(1).split()]
    p2s = {p: s for s, ps in s2p.items() for p in ps}

# ---- 省几何 ----
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

# ---- terrain.bmp 像素 → 每省原版地形 + 城市省 ----
tidx = np.asarray(Image.open(os.path.join(G, 'map', 'terrain.bmp')))
tbimg = Image.open(os.path.join(G, 'map', 'terrain.bmp'))
tb_palette = tbimg.getpalette()
flatp, flatt = prov.ravel(), tidx.ravel()
cnt = collections.defaultdict(collections.Counter)
for p, ix in zip(flatp.tolist(), flatt.tolist()):
    cnt[p][ix] += 1
orig_terrain, city_prov = {}, set()
for p, cc in cnt.items():
    types = collections.Counter()
    for ix, n in cc.items():
        typ = IDX2TYPE.get(ix)
        if typ:
            types[typ] += n
            if ix in SPAWN and n >= 5:
                city_prov.add(p)
    if types:
        orig_terrain[p] = types.most_common(1)[0][0]
print(f'原版地形覆盖省 {len(orig_terrain)}；城市省 {len(city_prov)}')

# ---- 4 邻域 ----
srcm = np.where(np.isin(prov, list(land_ids)), prov, 0)
adj4 = collections.defaultdict(set)
for a_, b_ in ((srcm[:, :-1], srcm[:, 1:]), (srcm[:-1, :], srcm[1:, :])):
    m = (a_ != b_) & (a_ > 0) & (b_ > 0)
    for x, y in zip(a_[m].tolist(), b_[m].tolist()):
        adj4[x].add(y)
        adj4[y].add(x)

# ---- 省均海拔（heightmap 存储序→视觉序后按省均值）----
hm = np.asarray(Image.open(os.path.join(G, 'map', 'heightmap.bmp')).convert('L')).astype(np.float64)
hm_vis_flat = hm[::-1].ravel()
order = np.argsort(flatp, kind='stable')
sp = flatp[order]
idx2 = np.searchsorted(sp, np.arange(int(flatp.max()) + 2))
alt_avg = {}
for pid in range(1, int(flatp.max()) + 1):
    lo, hi = idx2[pid], idx2[pid + 1]
    if hi > lo:
        alt_avg[pid] = float(hm_vis_flat[order[lo:hi]].mean())

# ---- 步骤1：全 plains ----
new_terr = {int(a[0]): ('plains' if kind.get(int(a[0])) == 'land' else a[6]) for _, a in rows}

# ---- 步骤2：国家覆盖 ----
for _, a in rows:
    pid = int(a[0])
    if kind.get(pid) != 'land':
        continue
    own = s2o.get(p2s.get(pid), '')
    if own in ('DRA', 'CYG'):
        new_terr[pid] = 'mountain'
    elif own == 'MHL':
        new_terr[pid] = 'hills'
    elif own in ('SGD', 'SDH', 'SGS'):
        new_terr[pid] = 'desert'

# ---- 步骤3：所有陆地省按地理特征（六国不豁免）----
for li, a in rows:
    pid = int(a[0])
    if kind.get(pid) != 'land':
        continue
    if pid in city_prov:
        new_terr[pid] = 'urban'
    elif orig_terrain.get(pid) == 'mountain':
        new_terr[pid] = 'mountain'
    elif a[5] == 'true':
        new_terr[pid] = 'plains'
    elif orig_terrain.get(pid) == 'forest':
        new_terr[pid] = 'forest'
    elif s2o.get(p2s.get(pid), '') in ('SGD', 'SDH', 'SGS'):
        new_terr[pid] = 'desert'
    else:
        new_terr[pid] = 'plains'

mount_final = set(p for p, v in new_terr.items() if v == 'mountain')
ALT_MIN = 105
hills_n = 0
for li, a in rows:
    pid = int(a[0])
    if kind.get(pid) != 'land' or new_terr[pid] != 'plains' or a[5] == 'true':
        continue
    nb_mount = any(q in mount_final for q in adj4.get(pid, ()))
    if nb_mount and alt_avg.get(pid, 0) >= ALT_MIN:
        new_terr[pid] = 'hills'
        hills_n += 1
dist = collections.Counter(new_terr.values())
print('最终地形分布:', dict(dist.most_common()), f'｜hills 补充 {hills_n}')

# ---- 落地 ----
if DRY:
    print('[DRY] definition.csv / terrain.bmp 未写盘')
    sys.exit(0)
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bdir = os.path.join(ROOT, '.backups', 'terrain_' + stamp)
os.makedirs(bdir, exist_ok=True)
# 把 new_terr 回写进 lines（此前遗漏此循环，导致 definition.csv 未被更新）
for li, a in rows:
    pid = int(a[0])
    if pid in new_terr and a[6] != new_terr[pid]:
        a[6] = new_terr[pid]
        lines[li] = ';'.join(a)

shutil.copy2(DEF, os.path.join(bdir, 'definition.csv'))
with open(DEF, 'w', encoding='utf-8', newline='') as fh:
    fh.write('\r\n'.join(lines))
print('definition.csv 已写入，备份', bdir)

tnew = tidx.copy()
for li, a in rows:
    pid = int(a[0])
    if kind.get(pid) == 'land':
        ix = TYPE2IDX.get(new_terr[pid])
        if ix is not None:
            tnew[prov == pid] = ix
out_img = Image.fromarray(tnew, 'P')
out_img.putpalette(tb_palette)
tbimg.close()
out_img.save(os.path.join(bdir, 'terrain_new.bmp'))
shutil.copy2(os.path.join(G, 'map', 'terrain.bmp'), os.path.join(bdir, 'terrain_old.bmp'))
shutil.copy2(os.path.join(bdir, 'terrain_new.bmp'), os.path.join(G, 'map', 'terrain.bmp'))
print('terrain.bmp 已重写并落回 mod（旧件备份 terrain_old.bmp）')

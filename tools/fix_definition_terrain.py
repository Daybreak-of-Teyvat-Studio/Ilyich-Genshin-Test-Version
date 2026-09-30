# -*- coding: utf-8 -*-
"""
修复 definition.csv 地形列（与 terrain.bmp 对齐）：
  以 terrain.bmp 每省像素的多数索引为准，反查地形名，写回 definition.csv 第 7 列。
原因：terrain_pipeline.py 缺少「new_terr → lines」回写循环，导致 10:16 起 definition.csv 未更新。
"""
import os, re, sys, shutil, datetime, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEF = os.path.join(G, 'map', 'definition.csv')
DRY = '--dry' in sys.argv

IDX2TYPE = {0: 'plains', 1: 'forest', 2: 'hills', 3: 'desert', 4: 'forest', 5: 'plains',
            6: 'mountain', 7: 'desert', 8: 'desert', 9: 'marsh', 10: 'mountain',
            11: 'mountain', 12: 'desert', 13: 'urban', 14: 'lakes', 15: 'ocean',
            16: 'mountain', 17: 'hills', 19: 'plains', 20: 'mountain', 21: 'jungle',
            22: 'jungle', 27: 'mountain', 31: 'mountain'}

# 读 definition
raw = open(DEF, 'rb').read()
text = raw.decode('utf-8-sig')
lines = text.split('\r\n')
rows = []
for li, l in enumerate(lines):
    a = l.split(';')
    if len(a) >= 8 and a[0].strip().isdigit():
        rows.append((li, a))

# 省位图 + terrain 索引
rgb2id = {}
for li, a in rows:
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
tb = np.asarray(Image.open(os.path.join(G, 'map', 'terrain.bmp')))

# 每省 → terrain.bmp 多数索引 → 地形名
newt, nopix, unknown = {}, [], []
for li, a in rows:
    pid = int(a[0])
    if a[4] != 'land':
        continue
    m = (prov == pid)
    if not m.any():
        nopix.append(pid)
        continue
    vals, cnts = np.unique(tb[m], return_counts=True)
    got = int(vals[np.argmax(cnts)])
    t = IDX2TYPE.get(got)
    if t is None:
        unknown.append((pid, got))
        continue
    newt[pid] = t

print(f'从 terrain.bmp 反推地形：{len(newt)} 个陆省'
      f'（无像素 {len(nopix)}、未知索引 {len(unknown)} {unknown[:5]}）')
before = collections.Counter(a[6] for _, a in rows if a[4] == 'land')
after = collections.Counter(newt.values())
print('definition.csv 当前分布:', dict(before.most_common()))
print('terrain.bmp  反推分布:', dict(after.most_common()))
diff = [pid for pid, t in newt.items() if t != dict((int(a[0]), a[6]) for _, a in rows)[pid]]
print(f'需改动的陆省: {len(diff)}')

if DRY:
    print('[DRY] 未写盘')
    sys.exit(0)

bdir = os.path.join(ROOT, '.backups', 'def_terrain_fix_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(DEF, os.path.join(bdir, 'definition.csv'))
n = 0
for li, a in rows:
    pid = int(a[0])
    if pid in newt and a[6] != newt[pid]:
        a[6] = newt[pid]
        lines[li] = ';'.join(a)
        n += 1
with open(DEF, 'w', encoding='utf-8', newline='') as fh:
    fh.write('\r\n'.join(lines))
print(f'definition.csv 已写入：改动 {n} 行，备份 {bdir}')

# 复验
bad = 0
for line in open(DEF, encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit() and a[4] == 'land':
        pid = int(a[0])
        if pid not in newt:
            continue
        m = (prov == pid)
        if not m.any():
            continue
        vals, cnts = np.unique(tb[m], return_counts=True)
        got = int(vals[np.argmax(cnts)])
        if IDX2TYPE.get(got) != a[6]:
            bad += 1
print(f'复验：definition.csv 地形 与 terrain.bmp 多数索引 不一致 = {bad}（应 0）')

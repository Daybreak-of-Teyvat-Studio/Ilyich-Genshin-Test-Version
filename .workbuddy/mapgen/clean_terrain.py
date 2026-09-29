# -*- coding: utf-8 -*-
"""terrain 索引图去碎片（一次性）：大块作种子，小块并入最近的种子。

用法： python clean_terrain.py --th=16 --out=...\\terrain_clean.bmp [--both=8,48]
"""
import os, io, time, sys, struct
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

G = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
M = os.path.join(G, 'map')
SRC = os.path.join(M, 'terrain.bmp')

_arg = {}
for a in sys.argv[1:]:
    if a.startswith('--') and '=' in a:
        k, v = a[2:].split('=', 1)
        _arg[k] = v
TH = int(_arg.get('th', 16))
OUT = _arg.get('out', os.path.join(M, 'terrain_clean.bmp'))
EXTRA = [int(x) for x in _arg.get('both', '').split(',') if x.strip()]
PRE = os.path.join(G, '.workbuddy', 'terrain_clean_preview', 'run_' + time.strftime('%m%d_%H%M%S'))
os.makedirs(PRE, exist_ok=True)

TYPE = {0: 'plains', 1: 'forest', 3: 'desert', 6: 'mountain', 9: 'marsh', 11: 'mountain',
        13: 'urban', 14: 'lakes', 15: 'ocean', 17: 'hills', 21: 'jungle'}
GUIDE = {0: (255, 129, 66), 1: (89, 199, 85), 3: (255, 63, 0), 6: (27, 27, 27),
         9: (76, 96, 35), 11: (124, 135, 125), 13: (155, 0, 255), 14: (0, 255, 255),
         15: (0, 0, 255), 17: (248, 255, 153), 21: (127, 191, 0)}

L = []
def P(s=''):
    L.append(str(s))

raw = open(SRC, 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
HDR = raw[:off]
a = np.array(Image.open(SRC)).astype(np.int16)
H, W = a.shape
labels = sorted(int(v) for v in np.unique(a))
P('输入 %s  %dx%d  偏移=%d  索引集 %s' % (os.path.basename(SRC), W, H, off, labels))
P('')

ST8 = np.ones((3, 3), bool)


def stats(arr):
    rows = []
    for l in labels:
        m = arr == l
        n = int(m.sum())
        if n == 0:
            rows.append((l, 0, 0, 0, 0, 0)); continue
        lab, k = ndi.label(m, ST8)
        sz = np.bincount(lab.ravel())[1:]
        rows.append((l, n, k, float(np.median(sz)), int(sz.max()), int((sz == 1).sum())))
    return rows


def show(arr, title):
    P('== %s ==' % title)
    P('   idx %-9s %9s %7s %7s %8s %8s' % ('', 'px', '块数', '中位块', '最大块', '孤立1px'))
    for l, n, k, med, mx, iso in stats(arr):
        P('   %-4d %-9s %9d %7d %7.0f %8d %8d' % (l, TYPE.get(l, '?'), n, k, med, mx, iso))
    tot = sum(x[2] for x in stats(arr))
    iso = sum(x[5] for x in stats(arr))
    P('   总块数 %d ；孤立单像素 %d' % (tot, iso))
    P('')


def clean(arr, th):
    seeds = np.zeros(arr.shape, bool)
    killed = {}
    for l in labels:
        m = arr == l
        if not m.any():
            continue
        lab, k = ndi.label(m, ST8)
        sz = np.bincount(lab.ravel())
        good = np.where((np.arange(len(sz)) > 0) & (sz > th))[0]
        if len(good):
            seeds |= np.isin(lab, good)
    keep = arr[seeds]
    P('   种子像素 %d (%.2f%%) ；非种子 %d' %
      (int(seeds.sum()), 100.0 * seeds.sum() / arr.size, int((~seeds).sum())))
    d, inds = ndi.distance_transform_edt(~seeds, return_indices=True)
    out = arr[inds[0], inds[1]].astype(np.int16)
    P('   非种子像素最大并入距离 %.1f px' % float(d.max()))
    return out


show(a, '去碎片前（当前 map/terrain.bmp）')

results = {}
for th in [TH] + EXTRA:
    P('################  阈值 th=%d  ################' % th)
    t0 = time.time()
    c = clean(a, th)
    P('   耗时 %.1f s' % (time.time() - t0))
    show(c, 'th=%d 去碎片后' % th)
    P('   改动像素 %d (%.3f%%)' % (int((c != a).sum()), 100.0 * (c != a).sum() / a.size))
    P('')
    results[th] = c

main = results[TH]
body = main.astype(np.uint8)[::-1, :].tobytes()
blob = bytearray(HDR + body)
struct.pack_into('<I', blob, 2, len(blob))
struct.pack_into('<I', blob, 34, len(body))
with open(OUT, 'wb') as f:
    f.write(bytes(blob))
im = Image.open(OUT)
P('写出 %s  (%d bytes)  mode=%s  回读一致=%s' %
  (os.path.basename(OUT), os.path.getsize(OUT), im.mode,
   bool((np.array(im) == main.astype(np.uint8)).all())))

for th in EXTRA:
    p = OUT.replace('.bmp', '_th%d.bmp' % th)
    b2 = bytearray(HDR + results[th].astype(np.uint8)[::-1, :].tobytes())
    struct.pack_into('<I', b2, 2, len(b2))
    struct.pack_into('<I', b2, 34, len(b2) - len(HDR))
    with open(p, 'wb') as f:
        f.write(bytes(b2))
    P('写出 %s  (%d bytes)' % (os.path.basename(p), os.path.getsize(p)))


def render(idx, step=1):
    rgb = np.zeros((idx.shape[0], idx.shape[1], 3), np.uint8)
    for l in labels:
        rgb[idx == l] = GUIDE.get(l, (255, 0, 255))
    return rgb[::step, ::step]


edge = np.zeros(a.shape, np.float32)
edge[:, :-1] += (a[:, :-1] != a[:, 1:]); edge[:, 1:] += (a[:, :-1] != a[:, 1:])
edge[:-1, :] += (a[:-1, :] != a[1:, :]); edge[1:, :] += (a[:-1, :] != a[1:, :])
dens = ndi.uniform_filter(edge, 128)
cy, cx = np.unravel_index(np.argmax(dens), dens.shape)
r0, r1 = max(0, cy - 140), min(H, cy + 140)
c0, c1 = max(0, cx - 190), min(W, cx + 190)
P('')
P('碎块最密处 y=%d x=%d ；裁剪 y=%d..%d x=%d..%d' % (cy, cx, r0, r1, c0, c1))
bf = render(a[r0:r1, c0:c1]); af = render(main[r0:r1, c0:c1])
gap = np.full((bf.shape[0], 6, 3), 255, np.uint8)
Image.fromarray(np.concatenate([bf, gap, af], axis=1)).save(os.path.join(PRE, 'crop_before_after.png'))
fb = render(a, 4); fa = render(main, 4)
gap2 = np.full((fb.shape[0], 6, 3), 255, np.uint8)
Image.fromarray(np.concatenate([fb, gap2, fa], axis=1)).save(os.path.join(PRE, 'full_before_after.png'))
open(os.path.join(PRE, 'crop_center.txt'), 'w').write('%d %d' % (cy, cx))
P('预览 -> %s' % PRE)

rep = os.path.join(G, '.workbuddy', 'terrain_clean_report_th%d_%s.txt' % (TH, time.strftime('%m%d_%H%M%S')))
io.open(rep, 'w', encoding='utf-8').write('\n'.join(L))
print('WROTE', rep)
print('OUT', OUT)

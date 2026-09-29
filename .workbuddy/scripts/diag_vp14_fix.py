# -*- coding: utf-8 -*-
"""14 个「坐标落海」省的完整报告 + 建议修复坐标（用该省最靠近质心的、高度>=96 的像素）。"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
MAP = os.path.join(MOD, 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_vp14_fix.txt')

BAD = [222, 674, 688, 774, 860, 1269, 1752, 2435, 2473, 3055, 3939, 4680, 4689, 4691]
L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

raw = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
rb = W * 3
a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:rb * H].reshape(H, W, 3)
prov = (a[:, :, 2].astype(np.int32) << 16) | (a[:, :, 1].astype(np.int32) << 8) | a[:, :, 0].astype(np.int32)
hmraw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
ho = struct.unpack_from('<I', hmraw, 10)[0]
hm = np.frombuffer(hmraw, dtype=np.uint8, offset=ho)[:W * H].reshape(H, W)
pid_rgb = {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) >= 5:
            try:
                pid_rgb[int(f2[0])] = (int(f2[1]), int(f2[2]), int(f2[3]))
            except ValueError:
                pass

pos = {}
cur = None; seen = False
for ln in open(os.path.join(MAP, 'positions.txt'), 'rb'):
    s = ln.decode('ascii', 'replace').strip()
    m = re.match(r'^(\d+)=\{$', s)
    if m:
        cur = int(m.group(1)); seen = False; continue
    if cur is not None and not seen:
        mm = re.match(r'^([\d.]+)\s+([\d.]+)\s+([\d.]+)$', s)
        if mm:
            pos[cur] = (float(mm.group(1)), float(mm.group(3))); seen = True

# 每个落海省：该省像素的范围 + 该省中「高度>=96 的像素」质心
P('=== 14 个落海胜利点省 · 详情与建议 ===')
P('')
newpos = {}
for pid in BAD:
    rgb = pid_rgb[pid]
    key = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
    mask = prov == key
    n = int(mask.sum())
    ys, xs = np.where(mask)
    onland = mask & (hm >= 96)
    nl = int(onland.sum())
    if nl:
        yl, xl = np.where(onland)
        tgt = (float(xl.mean()), float(yl.mean()))
    else:
        tgt = (float(xs.mean()), float(ys.mean()))
    cur_ = pos[pid]
    hnow = int(hm[int(cur_[1]), int(cur_[0])])
    hmin, hmax = int(hm[mask].min()), int(hm[mask].max())
    P(f'省 {pid}   definition rgb={rgb}  像素 {n}（陆地像素 {nl}）')
    P(f'   row 范围 {int(ys.min())}~{int(ys.max())}   col 范围 {int(xs.min())}~{int(xs.max())}')
    P(f'   现坐标 ({cur_[0]:.3f}, {cur_[1]:.3f})  该点高度 h={hnow}  → {"✗ 在水下(悬空)" if hnow < 96 else "✓ 在陆地"}')
    P(f'   建议坐标 ({tgt[0]:.3f}, {tgt[1]:.3f})  该点高度 h={int(hm[int(tgt[1]), int(tgt[0])])}')
    P('')
    newpos[pid] = tgt

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

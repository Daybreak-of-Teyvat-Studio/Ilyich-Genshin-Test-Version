# -*- coding: utf-8 -*-
"""coord_register.py —— 两版地图图像配准（真实陆地掩码 + 变换搜索）
输出最优 (sx, sy, ox, oy) 与真实陆地 IoU，并做关键探针"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None


def load_def(base):
    id2rgb, kind = {}, {}
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        a = l.strip().split(';')
        if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
            pid = int(a[0])
            id2rgb[pid] = (int(a[1]), int(a[2]), int(a[3]))
            kind[pid] = a[4]
    return id2rgb, kind


def to_prov(base):
    id2rgb, kind = load_def(base)
    arr = np.asarray(Image.open(os.path.join(base, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
    H, W = arr.shape[:2]
    key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    rgb2id = {((r << 16) | (g << 8) | b): pid for pid, (r, g, b) in id2rgb.items()}
    u, inv = np.unique(key, return_inverse=True)
    pl = np.zeros(len(u), np.int32)
    for i, k in enumerate(u):
        pl[i] = rgb2id.get(int(k), 0)
    prov = pl[inv].reshape(H, W)
    # 真实陆地掩码：省 kind == land
    land_ids = np.zeros(20001, bool)
    for pid, k in kind.items():
        if pid < 20001:
            land_ids[pid] = (k == 'land')
    land = land_ids[np.clip(prov, 0, 20000)]
    return prov, land, kind


bp, b_land, b_kind = to_prov(B)
gp, g_land, g_kind = to_prov(G)
Hb, Wb = bp.shape
Hg, Wg = gp.shape
print(f'beta {Wb}x{Hb} 陆地像素 {int(b_land.sum())}；gamma {Wg}x{Wg and Hg} 陆地像素 {int(g_land.sum())}')

# 降采样加速（beta→gamma 帧统一到 1024x368 网格）
SC = (1024, 368)
bl = np.asarray(Image.fromarray((b_land * 255).astype(np.uint8)).resize(SC, Image.BILINEAR)) > 127
gl = np.asarray(Image.fromarray((g_land * 255).astype(np.uint8)).resize(SC, Image.BILINEAR)) > 127
h, w = bl.shape


def score(sx, sy, ox, oy):
    """把 beta 掩码采样到 gamma 帧：gamma_px = beta_px * (sx, sy) + (ox, oy)（都在 1024 网格坐标）"""
    ys, xs = np.nonzero(bl)
    gx = np.round(xs * sx + ox).astype(int)
    gy = np.round(ys * sy + oy).astype(int)
    m = (gx >= 0) & (gx < w) & (gy >= 0) & (gy < h)
    if m.sum() == 0:
        return 0
    hit = gl[gy[m], gx[m]].sum()
    union = m.sum() + gl.sum() - hit
    return hit / union


# 粗搜
best = (0, 0, 0, 0, 0)
for sx in np.arange(0.85, 1.30, 0.025):
    for sy in np.arange(0.85, 1.30, 0.025):
        for ox in np.arange(-120, 121, 30):
            for oy in np.arange(-120, 121, 30):
                s = score(sx, sy, ox, oy)
                if s > best[4]:
                    best = (sx, sy, ox, oy, s)
print(f'粗搜最优: sx={best[0]:.3f} sy={best[1]:.3f} ox={best[2]} oy={best[3]} IoU={best[4]:.3f}')
# 精修
sx, sy, ox, oy = best[:4]
for _ in range(3):
    improved = False
    for dsx in (-0.02, -0.01, 0, 0.01, 0.02):
        for dsy in (-0.02, -0.01, 0, 0.01, 0.02):
            for dox in (-15, -8, 0, 8, 15):
                for doy in (-15, -8, 0, 8, 15):
                    s = score(sx + dsx, sy + dsy, ox + dox, oy + doy)
                    if s > best[4]:
                        best = (sx + dsx, sy + dsy, ox + dox, oy + doy, s)
                        improved = True
    sx, sy, ox, oy = best[:4]
    if not improved:
        break
print(f'精修最优: sx={best[0]:.4f} sy={best[1]:.4f} ox={best[2]:.1f} oy={best[3]:.1f} IoU={best[4]:.3f}')
print(f'（基准 5632→4096 为 sx={4096/5632:.4f}）')

# 保存变换（1024 网格 → 换算到 beta 全分辨率像素）
SXf = best[0] * 1024 / Wb
SYf = best[1] * 368 / Hb
OXf = best[2] * Wb / 1024
OYf = best[3] * Hb / 368
np.save(os.path.join(ROOT, 'tools', 'transform.npy'), np.array([SXf, SYf, OXf, OYf]))
print(f'全分辨率变换: beta_px * ({SXf:.4f}, {SYf:.4f}) + ({OXf:.1f}, {OYf:.1f}) → gamma_px')


def b2g_point(by, bx):
    gy = int(round(by * SYf + OYf))
    gx = int(round(bx * SXf + OXf))
    return gy, gx


def probe(bid):
    ys, xs = np.nonzero(bp == bid)
    if len(ys) == 0:
        return None
    idx = np.linspace(0, len(ys) - 1, min(30, len(ys))).astype(int)
    from collections import Counter
    votes = Counter()
    for i in idx:
        gy, gx = b2g_point(ys[i], xs[i])
        if 0 <= gy < Hg and 0 <= gx < Wg:
            g = int(gp[gy, gx])
            if g:
                votes[g] += 1
    if not votes:
        return None
    top, n = votes.most_common(1)[0]
    return top, round(n / sum(votes.values()), 2)


print()
print('=== 关键探针 ===')
for bid, note in ((1314, '高塔孤王（期望 442）'), (509, ''), (2397, ''), (4159, ''), (4236, ''), (1243, '')):
    r = probe(bid)
    if r:
        gid = r[0]
        print(f'  beta p{bid} → gamma p{gid}（{g_kind.get(gid, "?")}，置信 {r[1]}） {note}')
    else:
        print(f'  beta p{bid}: 无映射')

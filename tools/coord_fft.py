# -*- coding: utf-8 -*-
"""coord_fft.py —— FFT 相位相关配准（搜索 scale × translation）
判定两版地图是否为同一大陆的仿射变换关系，并求出最优变换。"""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None


def land_mask(base, out_w):
    id2rgb, kind = {}, {}
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        a = l.strip().split(';')
        if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
            pid = int(a[0])
            id2rgb[pid] = (int(a[1]), int(a[2]), int(a[3]))
            kind[pid] = a[4]
    arr = np.asarray(Image.open(os.path.join(base, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
    H, W = arr.shape[:2]
    key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    land_keys = np.array([(r << 16) | (g << 8) | b for pid, (r, g, b) in id2rgb.items()
                          if kind.get(pid) == 'land'], dtype=np.uint32)
    u, inv = np.unique(key, return_inverse=True)
    m = np.isin(u, land_keys)
    land = m[inv].reshape(H, W)
    im = Image.fromarray((land * 255).astype(np.uint8))
    ow = out_w
    oh = int(round(H * out_w / W))
    return np.asarray(im.resize((ow, oh), Image.BILINEAR)) > 100


bm = land_mask(B, 640)   # beta: 640x233
gm = land_mask(G, 640)   # gamma: 640x320
print(f'beta mask {bm.shape}，gamma mask {gm.shape}')


def warp(beta, sx, sy, canvas_h, canvas_w, ox=0, oy=0):
    """把 beta 掩码缩放 (sx, sy) 后放到画布 (偏移 ox, oy)"""
    h, w = beta.shape
    nh, nw = max(1, int(round(h * sy))), max(1, int(round(w * sx)))
    scaled = np.asarray(Image.fromarray((beta * 255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR)) > 100
    canvas = np.zeros((canvas_h, canvas_w), bool)
    y0 = max(0, oy)
    x0 = max(0, ox)
    ys = min(nh, canvas_h - oy)
    xs = min(nw, canvas_w - ox)
    if ys <= 0 or xs <= 0:
        return canvas
    canvas[y0:oy + ys, x0:ox + xs] = scaled[:ys, :xs]
    return canvas


sh, sw = gm.shape


def phase_shift(a, b):
    """a,b 同尺寸 bool → 最优整数平移（b 相对 a）"""
    fa = np.fft.rfft2(a.astype(np.float32))
    fb = np.fft.rfft2(b.astype(np.float32))
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    c = np.fft.irfft2(r, s=a.shape)
    idx = np.unravel_index(np.argmax(c), c.shape)
    dy, dx = idx
    if dy > a.shape[0] // 2:
        dy -= a.shape[0]
    if dx > a.shape[1] // 2:
        dx -= a.shape[1]
    return dy, dx


best = None
for sx in np.arange(0.70, 1.35, 0.05):
    for sy in np.arange(0.70, 1.35, 0.05):
        w = warp(bm, sx, sy, sh, sw, 0, 0)   # 先放左上，用相位相关求平移
        # 用更大的画布防越界
        big_h, big_w = int(sh * 1.6), int(sw * 1.6)
        wb = warp(bm, sx, sy, big_h, big_w, int(sw * 0.3), int(sh * 0.3))
        gb = np.zeros((big_h, big_w), bool)
        gb[:sh, :sw] = gm
        dy, dx = phase_shift(gb, wb)
        # wb 平移到与 gb 对齐：把 wb 平移 (-dy, -dx)
        w2 = np.roll(np.roll(wb, -dy, 0), -dx, 1)
        inter = (w2 & gb).sum()
        union = (w2 | gb).sum()
        iou = inter / union if union else 0
        if best is None or iou > best[0]:
            best = (iou, sx, sy, dx - int(sw * 0.3) if False else -dx + int(sw * 0.3), -dy + int(sh * 0.3))
            best = (iou, sx, sy, -dx, -dy)

print(f'最优: IoU={best[0]:.3f} sx={best[1]:.2f} sy={best[2]:.2f} 平移(dx={best[3]}, dy={best[4]}) [画布 {sh}x{sw} 坐标]')

# 精修 sx/sy
iou0, sx0, sy0, dx0, dy0 = best
for _ in range(2):
    for sx in np.arange(sx0 - 0.05, sx0 + 0.051, 0.01):
        for sy in np.arange(sy0 - 0.05, sy0 + 0.051, 0.01):
            big_h, big_w = int(sh * 1.6), int(sw * 1.6)
            wb = warp(bm, sx, sy, big_h, big_w, int(sw * 0.3), int(sh * 0.3))
            gb = np.zeros((big_h, big_w), bool)
            gb[:sh, :sw] = gm
            dy, dx = phase_shift(gb, wb)
            w2 = np.roll(np.roll(wb, -dy, 0), -dx, 1)
            inter = (w2 & gb).sum()
            union = (w2 | gb).sum()
            iou = inter / union if union else 0
            if iou > best[0]:
                best = (iou, sx, sy, -dx, -dy)
    iou0, sx0, sy0, dx0, dy0 = best
print(f'精修: IoU={best[0]:.3f} sx={best[1]:.3f} sy={best[2]:.3f}')
print('（>0.85 = 同大陆可坐标桥；<0.6 = 布局不同，坐标桥不可行）')

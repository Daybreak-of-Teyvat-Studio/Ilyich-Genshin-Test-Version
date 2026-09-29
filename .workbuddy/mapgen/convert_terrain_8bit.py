# -*- coding: utf-8 -*-
"""把 24 位 terrain.bmp 还原为 8 位索引图，颜色落到正确的调色板索引。

HOI4 判地形靠的是调色板索引(colormap ID)，不是 RGB。索引->地形的对应写在
原版 common/terrain/00_terrain.txt 的 terrain 块里。
"""
import os, io, time, struct
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

G = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
TMP = r'C:\Users\XIANGZIYUAN\hoi4lint\_git_terrain'
TS = time.strftime('%m%d_%H%M%S')
MAP = os.path.join(G, 'map')
CUR = os.path.join(MAP, 'terrain.bmp')
BASE8 = os.path.join(TMP, 'terrain_HEAD.bmp')
PRE = os.path.join(G, '.workbuddy', 'terrain_8bit_preview', 'run_' + TS)
BK = os.path.join(G, '.workbuddy', 'backup_20260924_terrain')
for d in (PRE, BK):
    os.makedirs(d, exist_ok=True)
L = []
def P(s=''):
    L.append(str(s))

W, H = 4096, 2048

# 颜色 -> 调色板索引（索引经原版 00_terrain.txt 核对，均指向正确的地形类别）
COL2IDX = {
    (255, 129, 66): 0,     # plains
    (89, 199, 85): 1,      # forest
    (248, 255, 153): 17,   # hills   (hills_blend)
    (127, 191, 0): 21,     # jungle  (jungle_18)
    (76, 96, 35): 9,       # marsh   (terrain_9)
    (124, 135, 125): 11,   # mountain
    (27, 27, 27): 6,       # mountain
    (255, 63, 0): 3,       # desert
    (0, 0, 255): 15,       # ocean
    (0, 255, 255): 14,     # lakes
    (155, 0, 255): 13,     # urban
    (128, 128, 128): 13,   # urban
}
IDX2TYPE = {0: 'plains', 1: 'forest', 3: 'desert', 6: 'mountain', 9: 'marsh', 11: 'mountain',
            13: 'urban', 14: 'lakes', 15: 'ocean', 17: 'hills', 21: 'jungle'}
IDX2TEX = {0: 1, 1: 4, 3: 9, 6: 11, 9: 6, 11: 11, 13: 10, 14: 255, 15: 9, 17: 2, 21: 4}

PAL = {i: (0, 0, 0) for i in range(255)}
PAL.update({0: (255, 129, 66), 1: (89, 199, 85), 3: (255, 63, 0), 6: (27, 27, 27),
            9: (76, 96, 35), 11: (124, 135, 125), 13: (155, 0, 255), 14: (0, 255, 255),
            15: (0, 0, 255), 17: (248, 255, 153), 21: (127, 191, 0)})

# ---------- 读当前 24 位图 ----------
cur = np.array(Image.open(CUR))
P('输入 %s  mode已按数组读取 shape=%s' % (os.path.basename(CUR), cur.shape))
assert cur.shape == (H, W, 3), cur.shape

# ---------- 分类 ----------
idx = np.full((H, W), -1, np.int16)
cnt = {}
for rgb, i in COL2IDX.items():
    m = (cur[..., 0] == rgb[0]) & (cur[..., 1] == rgb[1]) & (cur[..., 2] == rgb[2])
    n = int(m.sum())
    if n:
        idx[m] = i
        cnt[rgb] = n
P('')
P('=== 精确匹配到的颜色 ===')
for rgb, n in sorted(cnt.items(), key=lambda t: -t[1]):
    P('   %-18s -> idx %-3d (%-8s texture %-3d)  %d px' %
      (str(rgb), COL2IDX[rgb], IDX2TYPE[COL2IDX[rgb]], IDX2TEX[COL2IDX[rgb]], n))

unk = idx < 0
nu = int(unk.sum())
P('')
P('未精确匹配（抗锯齿/混色）像素 = %d  (%.4f%%)' % (nu, 100.0 * nu / idx.size))
if nu:
    d, inds = ndi.distance_transform_edt(unk, return_indices=True)
    idx[unk] = idx[inds[0][unk], inds[1][unk]]
    P('   已按最近邻已知像素归类，最大填充半径 = %.2f px' % float(d[unk].max()))
idx8 = idx.astype(np.uint8)

# ---------- 统计 ----------
P('')
P('=== 重建后的索引构成 ===')
u, c = np.unique(idx8, return_counts=True)
o = np.argsort(-c)
land = 0
for i in o:
    ii = int(u[i]); n = int(c[i])
    if ii != 15:
        land += n
    P('   idx %-3d %-8s texture %-3d  %9d px' % (ii, IDX2TYPE[ii], IDX2TEX[ii], n))
P('   陆地合计（不含 ocean）= %d px' % land)

# ---------- 组装 8 位 BMP ----------
raw = open(BASE8, 'rb').read()
hdr = bytearray(raw[:1074])
for i in range(255):
    r, g, b = PAL[i]
    hdr[54 + 4 * i + 0] = b
    hdr[54 + 4 * i + 1] = g
    hdr[54 + 4 * i + 2] = r
    hdr[54 + 4 * i + 3] = 0
body = idx8[::-1, :].tobytes()
blob = bytes(hdr) + body
P('')
P('  输出字节数 = %d （期望 1074 + %d = %d）' % (len(blob), W * H, 1074 + W * H))

def write_variant(pal_idx13, names):
    h = bytearray(hdr)
    for i in range(255):
        r, g, b = PAL[i]
        if i == 13:
            r, g, b = pal_idx13
        h[54 + 4 * i + 0] = b
        h[54 + 4 * i + 1] = g
        h[54 + 4 * i + 2] = r
        h[54 + 4 * i + 3] = 0
    data = bytes(h) + body
    for nm in names:
        p = os.path.join(MAP, nm)
        try:
            with open(p, 'wb') as f:
                f.write(data)
            P('   写出成功: %s (%d bytes)' % (nm, len(data)))
            return p, nm
        except Exception as e:
            P('   写出失败 %s: %s %s' % (nm, type(e).__name__, e))
    return None, None

P('')
P('=== 写出 ===')
main_path, main_name = write_variant((155, 0, 255), ['terrain.bmp', 'terrain_8bit.bmp'])
alt_path, alt_name = write_variant((128, 128, 128), ['terrain_8bit_graycity.bmp'])
P('')

# ---------- 回读校验 ----------
def verify(p, label, expect_idx13):
    im = Image.open(p)
    a = np.array(im)
    ok_idx = bool(a.shape == idx8.shape and (a == idx8).all())
    b = open(p, 'rb').read(64)
    off = struct.unpack('<I', b[10:14])[0]
    bpp = struct.unpack('<H', b[28:30])[0]
    w, h = struct.unpack('<ii', b[18:26])
    clr = struct.unpack('<I', b[46:50])[0]
    pal = im.getpalette()
    p13 = tuple(pal[13 * 3:13 * 3 + 3])
    P('   %-28s mode=%-3s %dx%d bpp=%d off=%d clrUsed=%d | 索引逐像素一致=%s | palette[13]=%s(期望%s)' %
      (label, im.mode, w, h, bpp, off, clr, ok_idx, p13, expect_idx13))
    return (im.mode == 'P' and bpp == 8 and ok_idx and p13 == expect_idx13)

if main_path:
    verify(main_path, main_name, (155, 0, 255))
if alt_path:
    verify(alt_path, alt_name, (128, 128, 128))

# ---------- 预览 ----------
def render(a8, name):
    rgb = np.zeros((H, W, 3), np.uint8)
    for i in range(255):
        m = a8 == i
        if m.any():
            rgb[m] = PAL[i]
    if name.startswith('gray'):
        rgb[a8 == 13] = (128, 128, 128)
    Image.fromarray(rgb[::4, ::4]).save(os.path.join(PRE, name))
    return rgb

old = np.array(Image.open(CUR))
new = render(idx8, 'after_gamma.png')
Image.fromarray(old[::4, ::4]).save(os.path.join(PRE, 'before_gamma.png'))
diff = (old != new).any(axis=2)
P('')
P('   预览: before_gamma.png / after_gamma.png ；画面差异 = %d px (%.4f%%)' %
  (int(diff.sum()), 100.0 * diff.sum() / diff.size))
ys, xs = np.where(diff)
if diff.any():
    P('   差异集中在 y=%d..%d x=%d..%d（即城市色块）' % (ys.min(), ys.max(), xs.min(), xs.max()))

# 备份当前 24 位文件
img = Image.open(CUR)
img.save(os.path.join(BK, 'terrain_24bit_%s.bmp' % TS))
img.save(os.path.join(BK, 'terrain_24bit_%s.png' % TS))
P('')
P('   备份 -> .workbuddy/backup_20260924_terrain/terrain_24bit_%s.bmp' % TS)

rep = os.path.join(G, '.workbuddy', 'terrain_8bit_report_%s.txt' % TS)
io.open(rep, 'w', encoding='utf-8').write('\n'.join(L))
print('WROTE', rep)
print('MAIN', main_name)

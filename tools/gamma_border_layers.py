# -*- coding: utf-8 -*-
"""
生成用于 PS 划分的文件（全部 4096x2048，与 provinces.bmp / 原版地图严格同坐标系）。

设计原则：线稿不压地形。
  · 省界/州界一律不加白晕（白晕会把颜色冲淡、并让线宽翻倍）
  · 省界给 3 档不透明度，按需选
  · 干净底图单独出 TIFF（LZW 无损），线稿当图层叠上去

输出到 Gamma_地图/分界图层/：
  底图_原版地图_无标注.tif        干净底图，LZW 无损
  省界线_淡_透明.png / _中_ / _实_  1px 省界，无晕，alpha 70/130/200
  州界线_透明.png                 2px 州界（洋红，无晕）
  叠加预览_淡.tif / 叠加预览_中.tif  省界+州界 flatten 到底图，LZW 无损
  细节_*.png                      1:1 原像素裁切（放大 2 倍仅为肉眼观察）
"""
import os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
OUT = os.path.join(ROOT, 'Gamma_地图', '分界图层')
os.makedirs(OUT, exist_ok=True)
FONTB = r'C:\Windows\Fonts\msyhbd.ttc'
SRC = r'C:\Users\LR\Desktop\hoi4ra2mod\提瓦特黎明\CEB643A617BDAF7A7B3089A8954A1332.bmp'

# ---------------- 省 / 州 掩膜 ----------------
state2provs = {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    state2provs[sid] = [int(x) for x in
                        re.search(r'provinces = \{([^}]*)\}', t).group(1).split()]

rgb2id, kind = {}, {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
        kind[int(a[0])] = a[4]

arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
pl = np.zeros(len(uniq), np.int32)
kl = np.zeros(len(uniq), np.uint8)
for i, k in enumerate(uniq):
    k = int(k)
    pid = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
    pl[i] = pid
    kl[i] = 1 if kind.get(pid, 'sea') == 'land' else 0
prov = pl[inv].reshape(H, W)
land = kl[inv].reshape(H, W).astype(bool)

slut = np.zeros(int(prov.max()) + 1, np.int32)
for s, ps in state2provs.items():
    for p in ps:
        if p < len(slut):
            slut[p] = s
state = slut[prov]

pb = np.zeros((H, W), bool)
pb[:, 1:] |= (prov[:, 1:] != prov[:, :-1])
pb[1:, :] |= (prov[1:, :] != prov[:-1, :])
pb &= land
sb = np.zeros((H, W), bool)
sb[:, 1:] |= (state[:, 1:] != state[:, :-1])
sb[1:, :] |= (state[1:, :] != state[:-1, :])
sb &= land


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx or dy:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def line_rgba(mask, color, alpha):
    """无晕线条层"""
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[mask] = (*color, alpha)
    return Image.fromarray(rgba, 'RGBA')


base = Image.open(SRC).convert('RGB')
print('底图:', base.size, base.mode)

# 干净底图（TIFF 无损）
base.save(os.path.join(OUT, '底图_原版地图_无标注.tif'), compression='tiff_lzw')
# 顺便覆盖旧的糊版 PNG
base.save(os.path.join(OUT, '底图_原版地图_无标注.png'))
print('底图_原版地图_无标注.tif 已出')

# ---------------- 省界线 3 档 ----------------
for name, a in [('淡', 70), ('中', 130), ('实', 200)]:
    line_rgba(pb, (0, 0, 0), a).save(os.path.join(OUT, f'省界线_{name}_透明.png'))
print('省界线 3 档已出')

# ---------------- 州界线（1px，靠颜色区分，不加粗）----------------
line_rgba(sb, (229, 0, 126), 220).save(os.path.join(OUT, '州界线_透明.png'))
print('州界线 已出')

# ---------------- 叠加预览 ----------------
pb_淡 = line_rgba(pb, (0, 0, 0), 70)
pb_中 = line_rgba(pb, (0, 0, 0), 130)
sb_l = line_rgba(sb, (229, 0, 126), 220)


def flatten(ls, name):
    comp = base.convert('RGBA')
    for l in ls:
        comp = Image.alpha_composite(comp, l)
    rgb = comp.convert('RGB')
    rgb.save(os.path.join(OUT, f'{name}.tif'), compression='tiff_lzw')
    rgb.save(os.path.join(OUT, f'{name}.png'))
    return rgb


for name, ls in [('叠加_省界淡', [pb_淡]),
                 ('叠加_省界中', [pb_中]),
                 ('叠加_省界淡+州界', [pb_淡, sb_l]),
                 ('叠加_省界中+州界', [pb_中, sb_l])]:
    flatten(ls, name)
print('叠加预览 已出')

# ---------------- 州号层 ----------------
flat = state.ravel()
gx = np.tile(np.arange(W, dtype=np.float64), H)
gy = np.repeat(np.arange(H, dtype=np.float64), W)
npix = np.bincount(flat, minlength=int(state.max()) + 2)
cx = np.bincount(flat, weights=gx, minlength=len(npix)) / np.maximum(npix, 1)
cy = np.bincount(flat, weights=gy, minlength=len(npix)) / np.maximum(npix, 1)
nums = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(nums)
f = ImageFont.truetype(FONTB, 13)
for sid in sorted(state2provs):
    d.text((int(round(cx[sid])), int(round(cy[sid]))), str(sid), font=f,
           fill=(15, 35, 110, 200), anchor='mm', stroke_width=1,
           stroke_fill=(255, 255, 255, 160))
nums.save(os.path.join(OUT, '州号_透明.png'))
print('州号层 已出')

# ---------------- 1:1 细节裁切（原像素，放大 2 倍仅为观察）----------------
for name, fn in [('底图无标注', '底图_原版地图_无标注.png'),
                 ('省界淡', '叠加_省界淡.png'),
                 ('省界中', '叠加_省界中.png'),
                 ('省界中+州界', '叠加_省界中+州界.png')]:
    im = Image.open(os.path.join(OUT, fn)).convert('RGB')
    for tag, box in [('蒙德', (2200, 1100, 2580, 1390)), ('须弥', (1700, 1450, 2080, 1740))]:
        im.crop(box).resize((760, 580), Image.NEAREST).save(
            os.path.join(OUT, f'细节1比1_{name}_{tag}.png'))
print('1:1 细节裁切 已出')
print('目录:', OUT)

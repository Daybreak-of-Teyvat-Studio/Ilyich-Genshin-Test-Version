# -*- coding: utf-8 -*-
"""出 terrain 8 位化前后的对比图与图例。"""
import os, glob
import numpy as np
from PIL import Image, ImageDraw

G = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
MAP = os.path.join(G, 'map')
runs = sorted(glob.glob(os.path.join(G, '.workbuddy', 'terrain_8bit_preview', 'run_*')))
PRE = runs[-1]
os.makedirs(PRE, exist_ok=True)

PAL = {0: (255, 129, 66), 1: (89, 199, 85), 3: (255, 63, 0), 6: (27, 27, 27),
       9: (76, 96, 35), 11: (124, 135, 125), 13: (155, 0, 255), 14: (0, 255, 255),
       15: (0, 0, 255), 17: (248, 255, 153), 21: (127, 191, 0)}
NAME = {0: 'plains', 1: 'forest', 3: 'desert', 6: 'mountain', 9: 'marsh', 11: 'mountain',
        13: 'urban', 14: 'lakes', 15: 'ocean', 17: 'hills', 21: 'jungle'}
TEX = {0: 1, 1: 4, 3: 9, 6: 11, 9: 6, 11: 11, 13: 10, 14: 255, 15: 9, 17: 2, 21: 4}

old = np.array(Image.open(os.path.join(MAP, 'terrain.bmp')))
new = np.array(Image.open(os.path.join(MAP, 'terrain_8bit.bmp')))
grayv = np.array(Image.open(os.path.join(MAP, 'terrain_8bit_graycity.bmp')))


def render(a, u13):
    rgb = np.zeros((a.shape[0], a.shape[1], 3), np.uint8)
    for i, c in PAL.items():
        m = a == i
        if m.any():
            rgb[m] = c
    if u13 != PAL[13]:
        rgb[a == 13] = u13
    return rgb


rn = render(new, (155, 0, 255))
rg = render(grayv, (128, 128, 128))

H, W = new.shape
SC = 4
sw, sh = W // SC, H // SC


def label(img, txt, xy=(10, 8)):
    d = ImageDraw.Draw(img)
    d.rectangle([xy[0] - 6, xy[1] - 6, xy[0] + 8 * len(txt) + 6, xy[1] + 22], fill=(255, 255, 255))
    d.text(xy, txt, fill=(0, 0, 0))


# 全图对比
a = Image.fromarray(old[::SC, ::SC]).convert('RGB')
b = Image.fromarray(rn[::SC, ::SC])
label(a, 'BEFORE: 24-bit RGB terrain.bmp')
label(b, 'AFTER: 8-bit indexed (correct IDs)')
cmpimg = Image.new('RGB', (sw, sh * 2 + 8), (255, 255, 255))
cmpimg.paste(a, (0, 0))
cmpimg.paste(b, (0, sh + 8))
cmpimg.save(os.path.join(PRE, 'compare_full.png'))

# 城市特写 1:1
crop = (1700, 400, 2300, 700)
x0, y0, x1, y1 = crop
tiles = [('BEFORE (24-bit, gray cities)', Image.fromarray(old[y0:y1, x0:x1])),
         ('AFTER (idx13 urban, purple)', Image.fromarray(rn[y0:y1, x0:x1])),
         ('ALT (idx13 urban, gray)', Image.fromarray(rg[y0:y1, x0:x1]))]
tw, th = x1 - x0, y1 - y0
zw = Image.new('RGB', (tw, (th + 26) * 3), (255, 255, 255))
for k, (t, im) in enumerate(tiles):
    z = Image.new('RGB', (tw, th + 26), (255, 255, 255))
    z.paste(im, (0, 26))
    label(z, t)
    zw.paste(z, (0, k * (th + 26)))
zw.save(os.path.join(PRE, 'zoom_cities.png'))

# 图例
LEY = ['idx  terrain   texture   rgb              px']
u, c = np.unique(new, return_counts=True)
for i in np.argsort(-c):
    ii = int(u[i])
    LEY.append('%-4d %-9s %-9d %-16s %d' % (ii, NAME[ii], TEX[ii], str(PAL[ii]), int(c[i])))
ley = Image.new('RGB', (560, 20 * len(LEY) + 20), (255, 255, 255))
d = ImageDraw.Draw(ley)
for k, t in enumerate(LEY):
    d.text((12, 12 + k * 20), t, fill=(0, 0, 0))
    if k:
        d.rectangle([8, 11 + k * 20, 16 + 0, 24 + k * 20], fill=PAL[int(u[np.argsort(-c)[k - 1]])])
ley.save(os.path.join(PRE, 'legend.png'))

print('PRE =', PRE)
for f in sorted(os.listdir(PRE)):
    print('  ', f)

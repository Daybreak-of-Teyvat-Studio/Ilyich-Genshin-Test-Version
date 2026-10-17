# -*- coding: utf-8 -*-
import os, io, sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
d = os.path.join(G, 'gfx', 'loadingscreens')
for f in sorted(os.listdir(d)):
    fp = os.path.join(d, f)
    h = io.open(fp, 'rb').read(8)
    try:
        im = Image.open(fp)
        info = f'PIL={im.format} {im.size}'
    except Exception as e:
        info = f'PIL失败 {e}'
    print(f'{f:28s} magic={h[:4]!r} {info}')

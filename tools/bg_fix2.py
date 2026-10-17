# -*- coding: utf-8 -*-
import os, io, sys, struct
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
LD = os.path.join(G, 'gfx', 'loadingscreens')
HDR = io.open(os.path.join(r'F:\Steam\steamapps\common\Hearts of Iron IV', 'gfx', 'loadingscreens', 'load_1_small.dds'), 'rb').read(128)
im = Image.open(os.path.join(LD, 'load_taog_ast.dds')).convert('RGB').resize((192, 144), Image.LANCZOS)
raw = im.tobytes()
px = bytearray(192 * 144 * 4)
for i in range(192 * 144):
    j = i * 4
    px[j:j + 4] = bytes((raw[i * 3 + 2], raw[i * 3 + 1], raw[i * 3], 255))
data = HDR + bytes(px)
for root in (G, L):
    d = os.path.join(root, 'gfx', 'loadingscreens')
    io.open(os.path.join(d, 'load_taog_ast_small.dds'), 'wb').write(data)
    extra = os.path.join(d, 'load_taog_ast_small_small.dds')
    if os.path.exists(extra):
        os.remove(extra)
print('taog small 已修正，多余文件已删')
print(Image.open(os.path.join(LD, 'load_taog_ast_small.dds')).size,
      os.path.getsize(os.path.join(LD, 'load_taog_ast_small.dds')), 'B')

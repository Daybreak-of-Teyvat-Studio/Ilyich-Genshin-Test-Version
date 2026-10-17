# -*- coding: utf-8 -*-
"""
修复两张背景相关 bug：
1) 缺失 GFX_button_238x38 -> 补进 core.gfx
2) 背景选择预览图不对 -> 为 mod 的每张加载图生成 192x144 的 _small.dds
   并让 mod 用同路径覆盖原版 interface/small_background.gfx
"""
import os, io, struct, shutil, sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
LD = os.path.join(G, 'gfx', 'loadingscreens')
HDR = io.open(os.path.join(V, 'gfx', 'loadingscreens', 'load_1_small.dds'), 'rb').read(128)
assert HDR[:4] == b'DDS ' and struct.unpack('<II', HDR[12:20]) == (144, 192)

names = sorted(os.path.splitext(f)[0] for f in os.listdir(LD) if f.lower().endswith('.dds'))
made = 0
for n in names:
    if n.endswith('_small'):
        src = os.path.join(LD, n[:-6] + '.dds')   # 从大图生成
    else:
        src = os.path.join(LD, n + '.dds')
    im = Image.open(src).convert('RGB').resize((192, 144), Image.LANCZOS)
    px = bytearray(192 * 144 * 4)
    raw = im.tobytes()
    for i in range(192 * 144):
        r, g, b = raw[i * 3], raw[i * 3 + 1], raw[i * 3 + 2]
        j = i * 4
        px[j], px[j + 1], px[j + 2], px[j + 3] = b, g, r, 255
    out = os.path.join(LD, n + '_small.dds')
    io.open(out, 'wb').write(HDR + bytes(px))
    made += 1
print(f'生成 _small.dds {made} 个')

# ---- 覆盖 small_background.gfx ----
lines = ['spriteTypes = {']
for n in names:
    s = n if n.endswith('_small') else n + '_small'
    lines += ['\tspriteType = {',
              f'\t\tname = "GFX_{s}"',
              f'\t\ttexturefile = "gfx/loadingscreens/{s}.dds"',
              '\t}', '']
lines += ['\tspriteType = {',
          '\t\tname = "GFX_frontend_loading_screen_border_small"',
          '\t\ttexturefile = "gfx/loadingscreens/loading_screen_border_small.dds"',
          '\t}', '}', '']
io.open(os.path.join(G, 'interface', 'small_background.gfx'), 'w',
        encoding='utf-8', newline='\r\n').write('\n'.join(lines))
print('写入 interface/small_background.gfx')

# ---- core.gfx 补 GFX_button_238x38 ----
cg = os.path.join(G, 'interface', 'core.gfx')
t = io.open(cg, 'rb').read().decode('utf-8-sig')
if 'GFX_button_238x38' in t:
    print('core.gfx 已有 GFX_button_238x38，跳过')
else:
    blk = ('\ttextSpriteType = {\r\n'
           '\t\tname = "GFX_button_238x38"\r\n'
           '\t\ttexturefile = "gfx/interface/button_238x38.dds"\r\n'
           '\t\teffectFile = "gfx/FX/buttonstate.lua"\r\n'
           '\t}\r\n\r\n')
    assert t.rstrip().endswith('}')
    i = t.rstrip().rfind('}')
    t = t[:i] + blk + t[i:]
    io.open(cg, 'w', encoding='utf-8', newline='').write(t)
    print('core.gfx 已补 GFX_button_238x38')

# ---- 双副本同步 ----
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
copied = 0
for n in names:
    s = n if n.endswith('_small') else n + '_small'
    fn = s + '.dds'
    shutil.copy2(os.path.join(LD, fn), os.path.join(L, 'gfx', 'loadingscreens', fn))
    copied += 1
os.makedirs(os.path.join(L, 'interface'), exist_ok=True)
for f in ('small_background.gfx', 'core.gfx'):
    shutil.copy2(os.path.join(G, 'interface', f), os.path.join(L, 'interface', f))
print(f'同步本地副本：{copied} 个 _small + small_background.gfx + core.gfx')

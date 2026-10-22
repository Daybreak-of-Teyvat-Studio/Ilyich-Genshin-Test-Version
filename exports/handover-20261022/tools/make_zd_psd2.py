# -*- coding: utf-8 -*-
"""make_zd_psd2.py —— 至冬三层 PSD：省图 / 省界线(中) / 底图(原版地图)
全部用同一 bbox 从 4096x2048 画布裁剪 → 像素级重合
输出: 桌面/Gamma至冬省图_双层.psd（覆盖旧版）"""
import os, sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
FJ = os.path.join(ROOT, '.ai_gamma_map', '分界图层')
OUT = os.path.join(os.path.expanduser('~'), 'Desktop', 'Gamma至冬省图_双层.psd')

x0, x1, y0, y1 = np.load(os.path.join(ROOT, 'tools', 'zd_bbox.npy'))
M = 40
box = (max(0, x0 - M), max(0, y0 - M), min(4096, x1 + M + 1), min(2048, y1 + M + 1))
print(f'裁剪框: {box}')

prov = np.asarray(Image.open(os.path.join(MOD, 'provinces.bmp')).convert('RGB').crop(box))
basemap = np.asarray(Image.open(os.path.join(FJ, '底图_原版地图_无标注.png')).convert('RGB').crop(box))
border = np.asarray(Image.open(os.path.join(FJ, '省界线_中_透明.png')).convert('RGBA').crop(box))
h, w = prov.shape[:2]
print(f'裁剪后: {w}x{h}')
assert prov.shape[:2] == basemap.shape[:2] == border.shape[:2]

from pytoshop.user import nested_layers
from pytoshop import enums
OPAQUE = np.full((h, w), 255, dtype=np.uint8)


def mk(name, rgb, alpha):
    return nested_layers.Image(
        name=name, visible=True, opacity=255, top=0, left=0,
        channels={0: rgb[:, :, 0].copy(), 1: rgb[:, :, 1].copy(), 2: rgb[:, :, 2].copy(),
                  -1: alpha},
    )


layers = [
    mk('省图', prov, OPAQUE),
    mk('省界线(中)', border[:, :, :3], border[:, :, 3].copy()),
    mk('底图', basemap, OPAQUE),
]  # 输入顺序 = 自顶向下（pytoshop 内部会反转）
psd = nested_layers.nested_layers_to_psd(layers, color_mode=enums.ColorMode.rgb,
                                         compression=enums.Compression.raw)
with open(OUT, 'wb') as f:
    psd.write(f)
print(f'已写入: {OUT}（{os.path.getsize(OUT) // 1024} KB）')

from pytoshop import core
with open(OUT, 'rb') as f:
    psd2 = core.PsdFile.read(f)
recs = psd2.layer_and_mask_info.layer_info.layer_records
print(f'验证: {psd2.width}x{psd2.height}, 图层 {len(recs)} 个（自底向上）')
for r in recs:
    print(f'  「{r.name}」 {r.width}x{r.height} @({r.left},{r.top})')

# 预览存档核对
Image.fromarray(prov).save(os.path.join(ROOT, 'tools', 'zd_prev_prov.png'))
Image.fromarray(basemap).save(os.path.join(ROOT, 'tools', 'zd_prev_base.png'))
bg = Image.new('RGB', (w, h))
bg.paste(Image.fromarray(basemap), (0, 0))
bg.paste(Image.fromarray(border), (0, 0), Image.fromarray(border))
bg.save(os.path.join(ROOT, 'tools', 'zd_prev_overlay.png'))
print('预览: tools/zd_prev_base.png / zd_prev_overlay.png')

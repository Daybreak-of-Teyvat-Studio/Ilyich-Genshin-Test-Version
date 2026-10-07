# -*- coding: utf-8 -*-
"""make_zd_psd.py —— 至冬省图 + 底图 双层 PSD（同 bbox 裁剪 → 边缘像素级重合）
输出: 桌面/Gamma至冬省图_双层.psd（上层=省图，下层=底图）"""
import os, sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
OUT = os.path.join(os.path.expanduser('~'), 'Desktop', 'Gamma至冬省图_双层.psd')

x0, x1, y0, y1 = np.load(os.path.join(ROOT, 'tools', 'zd_bbox.npy'))
M = 40
x0, x1 = max(0, x0 - M), x1 + M
y0, y1 = max(0, y0 - M), y1 + M
print(f'裁剪框: x {x0}-{x1}, y {y0}-{y1}（含 40px 边距）')

prov = Image.open(os.path.join(MOD, 'provinces.bmp')).convert('RGB').crop((x0, y0, x1 + 1, y1 + 1))
terr = Image.open(os.path.join(MOD, 'terrain.bmp')).convert('RGB').crop((x0, y0, x1 + 1, y1 + 1))
print(f'裁剪后: {prov.size[0]}x{prov.size[1]}')
assert prov.size == terr.size

prov_a = np.asarray(prov)
terr_a = np.asarray(terr)

from pytoshop.user import nested_layers
from pytoshop import enums


def mk_layer(name, rgb):
    h, w = rgb.shape[:2]
    return nested_layers.Image(
        name=name, visible=True, opacity=255, top=0, left=0,
        channels={0: rgb[:, :, 0].copy(), 1: rgb[:, :, 1].copy(), 2: rgb[:, :, 2].copy(),
                  -1: np.full((h, w), 255, dtype=np.uint8)},  # 显式 alpha，防 pytoshop 自动造 -1 常量通道
    )


# 列表顺序 = 自底向上：底图在下，省图在上
layers = [mk_layer('底图', terr_a), mk_layer('省图', prov_a)]
psd = nested_layers.nested_layers_to_psd(layers, color_mode=enums.ColorMode.rgb,
                                         compression=enums.Compression.raw)
with open(OUT, 'wb') as f:
    psd.write(f)
print(f'已写入: {OUT}（{os.path.getsize(OUT) // 1024} KB）')

# 验证：重新读取，确认图层数、名字、尺寸
from pytoshop import core
with open(OUT, 'rb') as f:
    psd2 = core.PsdFile.read(f)
    recs = psd2.layer_and_mask_info.layer_info.layer_records
    print(f'验证: {psd2.width}x{psd2.height}, 图层 {len(recs)} 个')
    for r in recs:
        print(f'  图层「{r.name}」 top={r.top} left={r.left} {r.width}x{r.height}')
im = Image.open(OUT)
print(f'PIL 读取: {im.size} {im.mode}（合成图）')

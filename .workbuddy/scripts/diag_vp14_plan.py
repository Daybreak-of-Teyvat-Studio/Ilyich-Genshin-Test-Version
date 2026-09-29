# -*- coding: utf-8 -*-
"""为 14 个落海省生成稳健修复坐标：取该省像素中「离质心最近的 h>=96 像素」。
输出新的 positions 块内容，供用户替换。"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
MAP = os.path.join(MOD, 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_vp14_plan.txt')

BAD = [222, 674, 688, 774, 860, 1269, 1752, 2435, 2473, 3055, 3939, 4680, 4689, 4691]
L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

raw = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
rb = W * 3
a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:rb * H].reshape(H, W, 3)
prov = (a[:, :, 2].astype(np.int32) << 16) | (a[:, :, 1].astype(np.int32) << 8) | a[:, :, 0].astype(np.int32)
hmraw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
ho = struct.unpack_from('<I', hmraw, 10)[0]
hm = np.frombuffer(hmraw, dtype=np.uint8, offset=ho)[:W * H].reshape(H, W)
pid_rgb = {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) >= 5:
            try:
                pid_rgb[int(f2[0])] = (int(f2[1]), int(f2[2]), int(f2[3]))
            except ValueError:
                pass

P('=== 建议修复坐标（离质心最近的 h>=96 像素）===')
P(f'{"pid":<8}{"现坐标":>22}{"现h":>5}  ->  {"新坐标":>22}{"新h":>5}{"像素数":>7}{"半径":>7}')
plan = {}
for pid in BAD:
    rgb = pid_rgb[pid]
    key = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
    mask = prov == key
    ys, xs = np.where(mask)
    hh = hm[ys, xs]
    cy, cx = ys.mean(), xs.mean()
    good = hh >= 96
    if good.any():
        gy, gx = ys[good], xs[good]
        d = (gy - cy) ** 2 + (gx - cx) ** 2
        k = int(np.argmin(d))
        ty, tx = int(gy[k]), int(gx[k])
        rad = float(np.sqrt(d[k]))
        ok = True
    else:
        k = int(np.argmin((ys - cy) ** 2 + (xs - cx) ** 2))
        ty, tx = int(ys[k]), int(xs[k])
        rad = 0.0
        ok = False
    newh = int(hm[ty, tx])
    plan[pid] = (tx, ty)
    # 现状
    import re as _re
    P(f'{pid:<8}{"":>22}{"":>5}  ->  ({tx:9.3f},{ty:9.3f}){newh:>5}{int(mask.sum()):>7}{rad:>7.2f}  {"OK" if ok else "无陆地像素!"}')

P('')
P('=== 各州首府标记（definition 第6列 true 的省就是这些）===')
P('   这 14 个全是 true（州首府）→ 胜利点图标画在首府，位置错就是悬空')

# 生成 positions.txt 补丁片段
P('')
P('=== positions.txt 需要替换的块（新坐标） ===')
for pid in BAD:
    tx, ty = plan[pid]
    P(f'{pid}={{\n\tposition={{\n\t\t{tx}.000 9.500 {ty}.000\n\t\t... 共 6 行\n\t}}\n\trotation={{ 6 行 0.000 }}\n\theight={{ 6 行 0.000 }}\n}}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

# 导出机器可读
import json
open(os.path.join(ROOT, '.workbuddy', 'vp14_plan.json'), 'w').write(json.dumps(plan))

# -*- coding: utf-8 -*-
"""拆解用户附图（terrain 渲染截图）的主色，与当前 terrain.bmp 调色板逐一对上。"""
import os, io, collections
import numpy as np
from PIL import Image

SHOT = r"C:\Users\XIANGZIYUAN\.workbuddy\clipboard-images\clipboard-2026-09-24T07-38-09-405Z-18d73347.jpg"
MAP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
REPORT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_shot.txt"
lines = []
P = lambda s='': lines.append(s)

# 当前 terrain.bmp 的调色板（上一步已读出）
CUR = {0: (255, 129, 66), 1: (89, 199, 85), 2: (0, 0, 0), 3: (255, 63, 0),
       6: (27, 27, 27), 9: (108, 198, 0), 11: (124, 135, 125), 13: (155, 0, 255),
       14: (0, 255, 255), 15: (0, 0, 255), 17: (248, 255, 153), 21: (127, 191, 0)}
CNT = {0: 33912, 1: 30953, 2: 5324, 3: 857, 6: 230410, 9: 133204, 11: 107497,
       13: 3662, 14: 782, 15: 7805978, 17: 9137, 21: 26892}
NAME = {0: "plains", 1: "forest", 2: "hills(黑)", 3: "desert", 6: "mountain(黑)",
        9: "marsh(改绿)", 11: "mountain(灰)", 13: "urban(紫)", 14: "lakes",
        15: "ocean", 17: "hills(浅黄)", 21: "jungle"}

im = Image.open(SHOT).convert("RGB")
A = np.array(im)
P(f"附图尺寸 {im.size}  mode={im.mode}")
flat = A.reshape(-1, 3)
c = collections.Counter(map(tuple, flat))
P("")
P("附图主色 top 22（原样）：")
for col, n in c.most_common(22):
    P(f"   {col}   {n:>9,} px   {n/flat.shape[0]*100:5.2f}%")

P("")
P("把附图颜色归到当前调色板（最近邻，阈值 40）：")
keys = np.array(list(CUR.values()), dtype=np.int32)
labs = list(CUR.keys())
sub = flat[::37].astype(np.int32)
d = ((sub[:, None, :] - keys[None, :, :]) ** 2).sum(axis=2)
lab = d.argmin(axis=1)
dist = np.sqrt(d.min(axis=1))
hit = dist < 40
cnt = collections.Counter(lab[hit].tolist())
tot = hit.sum()
P(f"   可归并像素占比 = {tot/len(lab)*100:.2f}%（其余是 JPEG 压缩与抗锯齿的过渡色）")
for k, n in cnt.most_common():
    idx = labs[k]
    P(f"   {NAME[idx]:14s} idx{idx:3d} 色{CUR[idx]}   img {n*37:>9,} px  ({n/tot*100:5.2f}%)  "
      f"| 图上真实 px {CNT[idx]:>9,}  比值 {n*37/CNT[idx]:.3f}")

P("")
P("逐通道确认有没有独立于调色板的灰度色：")
g = flat[(flat[:, 0] == flat[:, 1]) & (flat[:, 1] == flat[:, 2])]
P(f"   纯灰像素（R=G=B）共 {len(g):,}，占 {len(g)/flat.shape[0]*100:.2f}%")
gc = collections.Counter(map(int, g[:, 0]))
P(f"   灰阶分布 top12 = {gc.most_common(12)}")

# 找出图中偏"紫"（B 高、R 中、G 低）与偏"灰"（三通道接近且都中等）的像素量
r, gg, b = flat[:, 0].astype(int), flat[:, 1].astype(int), flat[:, 2].astype(int)
purple = (b > 120) & (r > 80) & (gg < 90) & (np.abs(r - b) < 160)
P(f"   偏紫像素 {int(purple.sum()):,}")
grayish = (np.abs(r - gg) < 20) & (np.abs(gg - b) < 20) & (r > 90) & (r < 180)
P(f"   偏灰（三通道接近、亮度中段）像素 {int(grayish.sum()):,}")

with io.open(REPORT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("ok")

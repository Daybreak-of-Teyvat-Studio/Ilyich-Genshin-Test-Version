# -*- coding: utf-8 -*-
"""对照 DOT MAP 3.0.bmp 检查 heightmap 的海陆掩膜与海面上限。"""
import os, io
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
D = os.path.join(GAMMA, ".workbuddy", "heightmap_soft")

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

ref = np.array(Image.open(os.path.join(GAMMA, ".workbuddy", "DOT MAP 3.0.bmp")))
ref_land = (ref[:, :, 0] == 150) & (ref[:, :, 1] == 68) & (ref[:, :, 2] == 192)
ref_sea = (ref[:, :, 0] == 5) & (ref[:, :, 1] == 20) & (ref[:, :, 2] == 18)
P("参照图: 陆地 %d px  海洋 %d px  其它未分类 %d px"
  % (ref_land.sum(), ref_sea.sum(), ref.size//3 - ref_land.sum() - ref_sea.sum()))

hm = np.array(Image.open(os.path.join(GAMMA, "map", "heightmap.bmp")))
hm_land = hm >= 94
P("当前 heightmap: 陆地(>=94) %d px  海洋 %d px" % (hm_land.sum(), (~hm_land).sum()))

P("")
P("掩膜逐像素完全一致: %s" % bool((ref_land == hm_land).all()))
d1 = ref_sea & hm_land
d2 = ref_land & ~hm_land
P("参照=海洋 而 heightmap=陆地 : %d px" % d1.sum())
P("参照=陆地 而 heightmap=海洋 : %d px" % d2.sum())
for nm, d in [("参照海洋/heightmap陆地", d1), ("参照陆地/heightmap海洋", d2)]:
    if d.sum():
        ys, xs = np.nonzero(d)
        P("   %s 的包围盒 y[%d,%d] x[%d,%d]，前 5 个坐标: %s"
          % (nm, ys.min(), ys.max(), xs.min(), xs.max(),
             list(zip(ys[:5].tolist(), xs[:5].tolist()))))
        P("   其 heightmap 灰度分布: %s" % dict(zip(*[x.tolist() for x in np.unique(hm[d], return_counts=True)])))

# 海面超限
sea_mask = ref_sea | (~hm_land)
over = (hm > 92) & sea_mask
P("")
P("参照图口径下'海洋'像素中，heightmap 灰度 > 92 的: %d px" % over.sum())
if over.sum():
    vals = hm[over]
    u, c = np.unique(vals, return_counts=True)
    P("   超限灰度分布: %s" % dict(zip(u.tolist(), c.tolist())))
    d_sea = ndi.distance_transform_edt(~ref_land)
    P("   超限像素的距岸距离分布: min=%.2f max=%.2f  (==1 的 %d 个)"
      % (d_sea[over].min(), d_sea[over].max(), int((np.abs(d_sea[over]-1) < 1e-6).sum())))

P("")
P("heightmap 海面(参照口径)灰度区间: min=%d max=%d  唯一值 %d 个"
  % (hm[sea_mask].min(), hm[sea_mask].max(), np.unique(hm[sea_mask]).size))
P("heightmap 陆地(参照口径)灰度区间: min=%d max=%d" % (hm[ref_land].min(), hm[ref_land].max()))

with io.open(os.path.join(D, "cmp_landmap.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep))
print("OK")

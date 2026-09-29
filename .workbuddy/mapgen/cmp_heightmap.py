# -*- coding: utf-8 -*-
import os, io
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
D = os.path.join(GAMMA, ".workbuddy", "heightmap_soft")
HM = os.path.join(GAMMA, "map", "heightmap.bmp")

orig = np.array(Image.open(HM))
new = np.load(os.path.join(D, "result.npy"))
land = orig >= 94
sea = ~land

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

def deltas(a, m):
    """4 邻域落差，只保留两端都在掩膜内、且不同区域标记处"""
    dv = np.abs(a[1:, :].astype(np.int16) - a[:-1, :].astype(np.int16))
    dh = np.abs(a[:, 1:].astype(np.int16) - a[:, :-1].astype(np.int16))
    mv = m[1:, :] & m[:-1, :]
    mh = m[:, 1:] & m[:, :-1]
    return np.concatenate([dv[mv], dh[mh]])

P("=== 陆地内部相邻落差（排除海陆交界） ===")
for name, a in [("原始", orig), ("柔化后", new)]:
    d = deltas(a, land)
    P("%-6s n=%d  mean=%.3f  p50=%.0f p90=%.0f p99=%.0f p99.9=%.0f max=%d"
      % (name, d.size, d.mean(), *np.percentile(d, [50, 90, 99, 99.9]), d.max()))
    P("        >=3: %d (%.3f%%)  >=5: %d  >=10: %d  >=20: %d"
      % ((d >= 3).sum(), 100.0*(d >= 3).mean(), (d >= 5).sum(), (d >= 10).sum(), (d >= 20).sum()))

P("")
P("=== 海洋内部相邻落差 ===")
for name, a in [("原始", orig), ("柔化后", new)]:
    d = deltas(a, sea)
    P("%-6s n=%d  max=%d  >=3: %d  >=5: %d" % (name, d.size, d.max(), (d >= 3).sum(), (d >= 5).sum()))

P("")
P("=== 海陆交界落差（应为 3：96 vs 93） ===")
dv = np.abs(new[1:, :].astype(np.int16) - new[:-1, :].astype(np.int16))
mv = land[1:, :] ^ land[:-1, :]
e = dv[mv]
u, c = np.unique(e, return_counts=True)
P("交界对数=%d  取值分布: %s" % (e.size, dict(zip(u.tolist(), c.tolist()))))

# 大落差位置分布
P("")
P("=== 柔化后 |Δ|>=10 的邻接对，按区域分类 ===")
dh = np.abs(new[:, 1:].astype(np.int16) - new[:, :-1].astype(np.int16))
for nm, mask, dd in [("陆地-陆地", land[:,1:] & land[:,:-1], dh),
                     ("海洋-海洋", sea[:,1:] & sea[:,:-1], dh),
                     ("陆地-海洋", land[:,1:] ^ land[:,:-1], dh)]:
    P("  %s: %d 对中有 %d 对 >=10 (max=%d)" % (nm, mask.sum(), int((dd[mask] >= 10).sum()), int(dd[mask].max()) if mask.any() else 0))

# 海面梯度剖面（沿一条远离陆地的射线实测）
P("")
P("=== 海面距离-灰度 实测剖面（对照规格 93/90/70/50/30/10 @ r=1/2/6/11/21/31） ===")
d_sea = ndi.distance_transform_edt(sea)
dsel = d_sea[sea]; vsel = new[sea].astype(np.float64)
for r in [1, 2, 3, 5, 6, 9, 11, 15, 21, 25, 31, 40, 60, 120, 400, 1660]:
    m = np.abs(dsel - r) < 0.05 if r < 31 else (dsel >= r)
    if m.sum() == 0:
        P("  r=%-5d 无像素" % r); continue
    P("  r=%-5d n=%-7d mean=%6.2f  median=%6.1f" % (r, int(m.sum()), vsel[m].mean(), np.median(vsel[m])))

P("")
P("=== 陆地随距岸距离的抬升（规格：d=1 -> 96） ===")
d_land = ndi.distance_transform_edt(land)
dl = d_land[land]; vl = new[land].astype(np.float64)
ol = orig[land].astype(np.float64)
for r in [1, 2, 3, 4, 6, 8, 10, 12, 16, 24, 40, 80, 160]:
    m = (np.floor(dl) == r) if r < 160 else (dl >= r)
    if m.sum() == 0:
        P("  d=%-4d 无像素" % r); continue
    P("  d=%-4d n=%-7d new_mean=%6.2f  orig_mean=%6.2f" % (r, int(m.sum()), vl[m].mean(), ol[m].mean()))

P("")
P("=== 全域统计 ===")
P("原始: min=%d max=%d  unique=%d" % (orig.min(), orig.max(), np.unique(orig).size))
P("柔化: min=%d max=%d  unique=%d" % (new.min(), new.max(), np.unique(new).size))
P("陆地占比: %.4f%%" % (100.0*land.mean()))

with io.open(os.path.join(D, "compare.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep))
print("OK")

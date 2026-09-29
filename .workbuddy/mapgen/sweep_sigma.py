# -*- coding: utf-8 -*-
"""陆地柔化强度扫描：不同 sigma 下的平滑度与峰高保留。"""
import os, io
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
HM = os.path.join(GAMMA, "map", "heightmap.bmp")

arr = np.array(Image.open(HM))
land = arr >= 94
f = arr.astype(np.float64)

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

def land_deltas(a):
    dv = np.abs(a[1:, :].astype(np.int16) - a[:-1, :].astype(np.int16))
    dh = np.abs(a[:, 1:].astype(np.int16) - a[:, :-1].astype(np.int16))
    mv = land[1:, :] & land[:-1, :]; mh = land[:, 1:] & land[:, :-1]
    return np.concatenate([dv[mv], dh[mh]])

d0 = land_deltas(arr)
P("原始       mean=%.2f p50=%.0f p90=%.0f p99=%.0f p99.9=%.0f max=%d  landmax=%d  >=10:%d"
  % (d0.mean(), *np.percentile(d0, [50,90,99,99.9]), d0.max(), arr[land].max(), (d0>=10).sum()))
P("")

d_land = ndi.distance_transform_edt(land).astype(np.float64)
for SIG in [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]:
    num = ndi.gaussian_filter(np.where(land, f, 0.0), SIG)
    den = ndi.gaussian_filter(land.astype(np.float64), SIG)
    blur = np.divide(num, np.maximum(den, 1e-9))
    t = np.clip((d_land - 1.0) / 11.0, 0.0, 1.0)
    sm = t*t*(3.0-2.0*t)
    lv = 96.0 + sm*(blur - 96.0)
    o = np.clip(np.rint(lv), 96, 255).astype(np.uint8)
    d = land_deltas(o)
    P("sigma=%-4.1f mean=%.2f p50=%.0f p90=%.0f p99=%.0f p99.9=%.0f max=%d  landmax=%d  >=10:%d  landmean=%.1f"
      % (SIG, d.mean(), *np.percentile(d, [50,90,99,99.9]), d.max(), o[land].max(), (d>=10).sum(), o[land].mean()))

with io.open(os.path.join(GAMMA, ".workbuddy", "heightmap_soft", "sweep.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(rep))
print("OK")

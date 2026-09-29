# -*- coding: utf-8 -*-
"""回读磁盘上的 heightmap.bmp 做终检，并出前后对比图。"""
import os, io, glob, struct, time
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
HM = os.path.join(GAMMA, "map", "heightmap.bmp")
D = os.path.join(GAMMA, ".workbuddy", "heightmap_soft")
BKD = os.path.join(GAMMA, ".workbuddy", "backup_20260924_heightmap")

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))


def save_png(img, path):
    try:
        img.save(path)
        return path
    except (PermissionError, OSError):
        alt = path[:-4] + "_%s.png" % time.strftime("%H%M%S")
        img.save(alt)
        return alt

orig_path = sorted(glob.glob(os.path.join(BKD, "heightmap_orig_*.bmp")))[-1]
orig = np.array(Image.open(orig_path))

im = Image.open(HM)
new = np.array(im)
raw = open(HM, "rb").read(38)
hs, w, h, pl, bpp, comp, isz = struct.unpack("<IiiHHII", raw[14:38])
P("落盘文件: mode=%s size=%s  bpp=%d comp=%d  bytes=%d  (原 %d)"
  % (im.mode, im.size, bpp, comp, os.path.getsize(HM), os.path.getsize(orig_path)))

land = orig >= 94
sea = ~land
P("掩膜与原图逐像素一致: %s" % bool(((new >= 94) == land).all()))
P("陆地 %d px / 海洋 %d px（海陆分布未改动）" % (land.sum(), sea.sum()))

P("")
P("【规则 1】所有陆地 >= 96 : %s   实测 min=%d max=%d" % (bool((new[land] >= 96).all()), new[land].min(), new[land].max()))
dl = ndi.distance_transform_edt(land)
rim = new[dl == 1]
P("【规则 2】沿海陆地 == 96 : %s   (d==1 的 %d 个像素全部=%d)" % (bool((rim == 96).all()), rim.size, int(rim.min())))
ds = ndi.distance_transform_edt(sea)
P("【规则 3】海面 <= 92 : %s   实测 max=%d min=%d" % (bool((new[sea] <= 92).all()), new[sea].max(), new[sea].min()))

P("")
P("【对照 .workbuddy\\DOT MAP 3.0.bmp】紫 #9644C0 = 陆地，黑 #051412 = 海洋")
ref = np.array(Image.open(os.path.join(GAMMA, ".workbuddy", "DOT MAP 3.0.bmp")))
ref_land = (ref[:, :, 0] == 150) & (ref[:, :, 1] == 68) & (ref[:, :, 2] == 192)
P("   参照图 陆地 %d px / 海洋 %d px" % (ref_land.sum(), (~ref_land).sum()))
P("   heightmap 掩膜与参照图逐像素一致 : %s" % bool((ref_land == land).all()))
P("   参照图'海洋'像素 > 92 的个数 : %d   （该区最大灰度 %d）" % (int((new[~ref_land] > 92).sum()), new[~ref_land].max()))
P("   参照图'陆地'像素 < 96 的个数 : %d   （该区最小灰度 %d）" % (int((new[ref_land] < 96).sum()), new[ref_land].min()))

P("")
P("【规则 4】海面距离-灰度（距最近陆地欧氏距离 r 处的实测值）")
P("      r      规格      实测mean  实测median     n")
spec = {1: 92, 2: 90, 6: 70, 11: 50, 21: 30}
dsel = ds[sea]; vsel = new[sea].astype(np.float64)
for r in sorted(spec):
    m = np.abs(dsel - r) < 0.001
    P("   %4d      %3d      %7.2f   %8.1f   %6d" % (r, spec[r], vsel[m].mean(), np.median(vsel[m]), m.sum()))
for r in [31, 41, 60, 200, 800]:
    m = dsel >= r
    P("   >=%-4d      -       %7.2f   %8.1f   %6d" % (r, vsel[m].mean(), np.median(vsel[m]), m.sum()))

P("")
P("【规则 5】落差（4 邻域）")
dv = np.abs(new[1:, :].astype(np.int16) - new[:-1, :].astype(np.int16))
dh = np.abs(new[:, 1:].astype(np.int16) - new[:, :-1].astype(np.int16))
edge = dv[land[1:, :] ^ land[:-1, :]]
u, c = np.unique(np.concatenate([edge, np.abs(new[:,1:].astype(np.int16)-new[:,:-1].astype(np.int16))[land[:,1:]^land[:,:-1]]]), return_counts=True)
P("   海陆交界落差取值: %s  （规格：陆地96 - 海面93 = 3）" % dict(zip(u.tolist(), c.tolist())))
ll_v = dv[land[1:, :] & land[:-1, :]]; ll_h = dh[land[:, 1:] & land[:, :-1]]
ll = np.concatenate([ll_v, ll_h])
oo = np.concatenate([dv[sea[1:, :] & sea[:-1, :]], dh[sea[:, 1:] & sea[:, :-1]]])
P("   陆地内部: mean=%.2f  p90=%.0f p99=%.0f  max=%d    (原图 mean=%.2f p90=%.0f p99=%.0f max=%d)"
  % (ll.mean(), *np.percentile(ll, [90, 99]), ll.max(),
     np.concatenate([np.abs(orig[1:,:].astype(np.int16)-orig[:-1,:].astype(np.int16))[land[1:,:]&land[:-1,:]],
                     np.abs(orig[:,1:].astype(np.int16)-orig[:,:-1].astype(np.int16))[land[:,1:]&land[:,:-1]]]).mean(),
     *np.percentile(np.concatenate([np.abs(orig[1:,:].astype(np.int16)-orig[:-1,:].astype(np.int16))[land[1:,:]&land[:-1,:]],
                     np.abs(orig[:,1:].astype(np.int16)-orig[:,:-1].astype(np.int16))[land[:,1:]&land[:,:-1]]]), [90, 99]),
     np.concatenate([np.abs(orig[1:,:].astype(np.int16)-orig[:-1,:].astype(np.int16))[land[1:,:]&land[:-1,:]],
                     np.abs(orig[:,1:].astype(np.int16)-orig[:,:-1].astype(np.int16))[land[:,1:]&land[:,:-1]]]).max()))
P("   海洋内部: mean=%.2f max=%d  (近岸按规格陡降，最大 5)" % (oo.mean(), oo.max()))
P("   全图最大落差: %d  （原图 103，其中 >16 的对数：原 %d，现 %d）"
  % (max(dv.max(), dh.max()), int((np.concatenate([dv.ravel(), dh.ravel()]) >= 16).sum()),
     int((np.concatenate([dv.ravel(), dh.ravel()]) >= 16).sum())))

P("")
P("【灰阶使用】原 %d 个 -> 现 %d 个；陆地 %d..%d，海面 %d..93"
  % (np.unique(orig).size, np.unique(new).size, new[land].min(), new[land].max(), new[sea].min()))

# ---- 对比图 ----
def strip(a, y0, x0, s):
    return a[y0:y0+s, x0:x0+s]
_c1 = save_png(Image.fromarray(np.concatenate([orig, new], axis=0), mode="L"), os.path.join(D, "compare_full.png"))
y0, x0, s = 64, 1728, 512
zoom = np.concatenate([strip(orig, y0, x0, s), strip(new, y0, x0, s)], axis=1)
_c2 = save_png(Image.fromarray(zoom, mode="L").resize((s*2, s), Image.NEAREST), os.path.join(D, "compare_zoom.png"))
P("")
P("对比图: %s（上=原图 下=柔化后）；%s（左=原 右=新, y=%d x=%d 512px）"
  % (os.path.basename(_c1), os.path.basename(_c2), y0, x0))

# ---- 派生文件提醒 ----
wn = os.path.join(GAMMA, "map", "world_normal.bmp")
P("")
P("派生文件: world_normal.bmp 存在=%s  mtime=%s" % (os.path.isfile(wn),
  __import__("time").strftime("%Y-%m-%d %H:%M:%S", __import__("time").localtime(os.path.getmtime(wn))) if os.path.isfile(wn) else "-"))

with io.open(os.path.join(D, "verify.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep))
print("OK")

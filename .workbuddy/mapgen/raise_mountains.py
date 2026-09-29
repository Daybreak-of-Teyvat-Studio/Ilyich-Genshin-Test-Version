# -*- coding: utf-8 -*-
"""把高度图的山地整体抬升，并把灰度上限提到 220；龙脊雪山（DRA 所辖州）额外加强。

规则
  1) 山地起点 TH = 125（与 terrain 涂山地的阈值一致）。
  2) 全局提升量随高度线性增长：h=125 时 +1，h=当前最高 187 时 +20，区间内单调连续。
  3) 龙脊雪山（DRA 33 个省的像素并集）叠加一个额外加成，加成的空间权重由核心区向外羽化，
     使得该区峰顶刚好到达 CAP = 220；加成按高度加权，低处不加。
  4) 全程 clamp 到 220；不触碰 h < 125 的像素，海面与海岸规格不变。

用法: python raise_mountains.py --out=<路径> [--th=125] [--cap=220] [--rlo=1] [--rhi=20] [--feather=45]
"""
import os, io, re, sys, time, struct
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
M = os.path.join(G, "map")
H = os.path.join(G, ".workbuddy")
HM = os.path.join(M, "heightmap.bmp")
BKD = os.path.join(H, "backup_heightmap_raise")

_arg = lambda k, d: ([x for x in sys.argv if x.startswith("--%s=" % k)] or ["--%s=%s" % (k, d)])[0].split("=", 1)[1]
OUT = _arg("out", os.path.join(M, "heightmap_v2.bmp"))
TH = int(_arg("th", 125))
CAP = int(_arg("cap", 220))
RLO = int(_arg("rlo", 1))
RHI = int(_arg("rhi", 20))
FEATHER = int(_arg("feather", 45))

# DRA 诸州（取自 Gamma州列表.xlsx，2026-09-24 版本）
DRA_STATES = {
    533: [95, 284, 811, 993, 1221, 1271, 1342, 2271, 3677, 3701, 3711, 3731],
    534: [813, 964, 1236, 1463, 1467, 1513, 3662, 3727],
    547: [4, 925, 1223, 1592, 1870, 2062, 2085, 3696, 3732, 3750, 3754],
    565: [3743, 3765],
}

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

P("heightmap 源 : %s (%s)" % (HM, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(HM)))))
P("输出         : %s" % OUT)
P("参数: 阈值=%d 上限=%d 全局提升=%d..%d 羽化=%dpx" % (TH, CAP, RLO, RHI, FEATHER))
P("")

hm = np.array(Image.open(HM))
assert hm.ndim == 2, hm.shape
H0, W = hm.shape
P("尺寸 %dx%d  min=%d max=%d" % (W, H0, hm.min(), hm.max()))

# ---------- 1. 建 DRA 像素掩膜 ----------
id2rgb = {}
with io.open(os.path.join(M, "definition.csv"), "r", encoding="utf-8-sig", errors="replace") as f:
    for line in f:
        p = line.strip().split(";")
        if len(p) >= 4:
            try:
                id2rgb[int(p[0])] = (int(p[1]), int(p[2]), int(p[3]))
            except ValueError:
                pass

prov = np.array(Image.open(os.path.join(M, "provinces.bmp")))
packed = (prov[:, :, 0].astype(np.uint32) << 16) | (prov[:, :, 1].astype(np.uint32) << 8) | prov[:, :, 2].astype(np.uint32)

mask = np.zeros(hm.shape, dtype=bool)
P("== DRA 各省命中像素 ==")
tot = 0
for sid, plist in DRA_STATES.items():
    row = []
    for pid in plist:
        c = id2rgb.get(pid)
        if c is None:
            row.append("%d:MISSING" % pid)
            continue
        n = int((packed == ((c[0] << 16) | (c[1] << 8) | c[2])).sum())
        mask |= (packed == ((c[0] << 16) | (c[1] << 8) | c[2]))
        tot += n
        row.append("%d:%d" % (pid, n))
    P("  州 %d (%d 省): %s" % (sid, len(plist), " ".join(row)))
ys, xs = np.where(mask)
P("DRA 掩膜合计 = %d px，包围盒 y=%d..%d x=%d..%d" % (int(mask.sum()), ys.min(), ys.max(), xs.min(), xs.max()))
P("")

# ---------- 2. 全局提升 ----------
h = hm.astype(np.float64)
hmax = int(hm.max())
t = np.clip((h - TH) / float(hmax - TH), 0.0, 1.0)
raise_g = np.where(h >= TH, RLO + (RHI - RLO) * t, 0.0)
P("全局提升: h=%d -> +%d, h=%d -> +%.2f, h=%d -> +%d" % (TH, RLO, 150, RLO + (RHI - RLO) * (150 - TH) / float(hmax - TH), hmax, RHI))

# ---------- 3. 龙脊雪山额外加成 ----------
core = ndi.binary_erosion(mask, np.ones((3, 3)), iterations=3)
d = ndi.distance_transform_edt(~core)
w = np.clip(1.0 - d / float(FEATHER), 0.0, 1.0)
w = ndi.gaussian_filter(w, 6)
w = np.clip(w / max(1e-9, w[core].max()), 0.0, 1.0)

ds_max = int(hm[mask].max())
base_at_dsmax = float(raise_g[mask].max())
extra_cap = float(CAP) - (ds_max + base_at_dsmax)
g = np.clip((h - TH) / float(ds_max - TH), 0.0, 1.0)
extra = np.maximum(0.0, extra_cap) * g * w
P("龙脊雪山: 区内最高 %d，全局提升在该处 %.2f，为达 %d 的额外加成 = %.2f" % (ds_max, base_at_dsmax, CAP, extra_cap))
P("羽化权重: 区内最大 %.3f，区内最小 %.3f，>0 的像素 %d" % (w[mask].max(), w[mask].min(), int((w > 0).sum())))
P("")

# ---------- 4. 合成 ----------
new = h + raise_g + extra
new = np.minimum(new, CAP)
new = np.rint(new).astype(np.uint8)

d_raise = new.astype(np.int16) - hm.astype(np.int16)
P("== 结果 ==")
P("原图 min=%d max=%d  ->  新图 min=%d max=%d" % (hm.min(), hm.max(), new.min(), new.max()))
P("被改像素 %d（应恰为 h>=%d 的集合）" % (int((d_raise != 0).sum()), TH))
P("改动集合 == (h>=%d): %s" % (TH, bool(((d_raise != 0) == (hm >= TH)).all())))
P("提升量  min=%d max=%d  均值(改动区) %.2f" % (d_raise[d_raise != 0].min() if (d_raise != 0).any() else 0,
                                            d_raise.max(), d_raise[d_raise != 0].mean() if (d_raise != 0).any() else 0))
P("h<%d 是否完全未动: %s" % (TH, bool((new[hm < TH] == hm[hm < TH]).all())))
P("单调性(新值随旧值不降): %s" % bool(np.all(np.diff(new[hm >= TH].astype(np.int16)[np.argsort(hm[hm >= TH], kind="stable")]) >= 0)))
P("")
P("== 海面/海岸规格复核 ==")
sea_old = hm[hm <= 93]; sea_new = new[hm <= 93]
P("原海面 max=%d；新图对应处 max=%d" % (int(sea_old.max()), int(sea_new.max())))
land_o = hm >= 94
P("原陆地 min=%d；新图陆地 min=%d（要求 >=96）" % (int(hm[land_o].min()), int(new[land_o].min())))
P("")
P("== 龙脊雪山范围 ==")
P("区内 min=%d max=%d（原 %d..%d）" % (int(new[mask].min()), int(new[mask].max()), int(hm[mask].min()), ds_max))
P("区内达到 %d 的像素 = %d" % (CAP, int((new[mask] == CAP).sum())))
P("")
P("== 全图高段对比 ==")
for t2 in (140, 150, 160, 170, 180, 190, 200, 210, 220):
    P("  >=%3d : 原 %6d  ->  新 %6d" % (t2, int((hm >= t2).sum()), int((new >= t2).sum())))
P("")
P("== 全图最高 10 块连通区（新图 >=190）==")
m2 = new >= 190
lab, n = ndi.label(m2, np.ones((3, 3)))
if n:
    sz = np.bincount(lab.ravel())[1:]
    for i in np.argsort(-sz)[:10]:
        yy, xx = np.where(lab == i + 1)
        P("  %6d px  y=%d..%d x=%d..%d  峰值 %d%s" % (sz[i], yy.min(), yy.max(), xx.min(), xx.max(), int(new[lab == i + 1].max()),
                                                      "   <= 龙脊雪山" if mask[lab == i + 1].any() else ""))

# ---------- 5. 备份 + 写出 ----------
os.makedirs(BKD, exist_ok=True)
bak = os.path.join(BKD, "heightmap_orig_%s.bmp" % time.strftime("%Y%m%d_%H%M%S"))
raw = open(HM, "rb").read()
PXOFF = struct.unpack("<I", raw[10:14])[0]        # 像素数据起始偏移（含调色板）
if not os.path.isfile(bak):
    open(bak, "wb").write(raw)
    P("")
    P("已备份原 heightmap -> %s" % bak)

blob = bytearray(raw[:PXOFF] + new[::-1, :].tobytes())   # 8bit 索引图：行自下而上，调色板原样保留
struct.pack_into("<I", blob, 2, len(blob))                # bfSize
struct.pack_into("<I", blob, 34, len(blob) - PXOFF)       # biSizeImage
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(bytes(blob))
P("像素数据偏移 = %d，调色板字节数 = %d" % (PXOFF, PXOFF - 54))
P("已写出 %s (%d bytes)" % (OUT, os.path.getsize(OUT)))

# ---------- 6. 回读自校验 ----------
chk = np.array(Image.open(OUT))
P("")
P("回读校验: shape=%s  min=%d max=%d" % (chk.shape, chk.min(), chk.max()))
P("与新图完全一致: %s" % bool((chk == new).all()))
P("与旧图差异像素: %d（应 == %d）" % (int((chk != hm).sum()), int((hm >= TH).sum())))

# ---------- 7. 预览 ----------
RUN = time.strftime("%m%d_%H%M%S")
APPDIR = os.path.join(H, "heightmap_raise_preview", "run_" + RUN)
os.makedirs(APPDIR, exist_ok=True)

def shade(a):
    a = a.astype(np.float64)
    gy, gx = np.gradient(a)
    return np.clip(128 + (gx - gy) * 1.5, 0, 255).astype(np.uint8)

sheet = Image.new("L", (1024, 512 * 2 + 8), 0)
sheet.paste(Image.fromarray(shade(hm)).resize((1024, 512), Image.LANCZOS), (0, 0))
sheet.paste(Image.fromarray(shade(new)).resize((1024, 512), Image.LANCZOS), (0, 520))
try:
    sheet.save(os.path.join(APPDIR, "hillshade_before_after.png"))
except Exception as e:
    P("预览保存失败: %s" % e)

cy, cx = int(ys.mean()), int(xs.mean())
half = 420
y0 = max(0, min(H0 - half * 2, cy - half)); x0 = max(0, min(W - half * 2, cx - half))
z = Image.new("L", (half * 2 * 2 + 8, half * 2), 0)
z.paste(Image.fromarray(shade(hm[y0:y0 + half * 2, x0:x0 + half * 2])), (0, 0))
z.paste(Image.fromarray(shade(new[y0:y0 + half * 2, x0:x0 + half * 2])), (half * 2 + 8, 0))
try:
    z.save(os.path.join(APPDIR, "hillshade_dragonspine.png"))
except Exception as e:
    P("放大图保存失败: %s" % e)
P("龙脊雪山取景 y0=%d x0=%d 边长 %d" % (y0, x0, half * 2))

io.open(os.path.join(H, "heightmap_raise_report_%s.txt" % RUN), "w", encoding="utf-8").write("\n".join(rep))
print("DONE " + APPDIR)

# -*- coding: utf-8 -*-
"""为「海面重塑 + 陆地柔化」出一组对比与剖面图（只读，不写地图目录）。"""
import os, io, time
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
M = os.path.join(G, "map")
A_PATH = os.path.join(M, "heightmap.bmp")             # 改造前（新主图：海面恒 89、陆地基准 100）
B_PATH = os.path.join(M, "heightmap_v3_new.bmp")      # 改造后（生效中）
RUN = time.strftime("%m%d_%H%M%S")
OUT = os.path.join(G, ".workbuddy", "heightmap_sea", "compare_" + RUN)
os.makedirs(OUT, exist_ok=True)

A = np.array(Image.open(A_PATH))
B = np.array(Image.open(B_PATH))
land = A >= 94
sea = ~land
d_sea = ndi.distance_transform_edt(sea)
d_land = ndi.distance_transform_edt(land)

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

def save_png(img, name):
    p = os.path.join(OUT, name)
    try:
        img.save(p); return p
    except (PermissionError, OSError):
        p = os.path.join(OUT, name[:-4] + "_%s.png" % time.strftime("%H%M%S"))
        img.save(p); return p

# ---- 1) 全图前后（2x 缩小后上下拼） ----
a_full = np.array(Image.fromarray(A, mode="L").resize((1024, 512), Image.BILINEAR))
b_full = np.array(Image.fromarray(B, mode="L").resize((1024, 512), Image.BILINEAR))
sep = np.full((8, 1024), 70, dtype=np.uint8)
save_png(Image.fromarray(np.concatenate([a_full, sep, b_full], axis=0), mode="L"),
         "full_before_after.png")

# ---- 2) 海岸 1:1 放大前后（同一窗口，左右并排） ----
step = 64
ch_, cw_ = 2048 // step, 4096 // step
cell = land[:ch_*step, :cw_*step].reshape(ch_, step, cw_, step).mean(axis=(1, 3))
W = 8; best, bpos = -1, (0, 0)
for i in range(ch_ - W):
    for j in range(cw_ - W):
        blk = cell[i:i+W, j:j+W]; f = blk.mean()
        if 0.30 < f < 0.75:
            s = blk.max() - blk.min()
            if s > best: best, bpos = s, (i, j)
cy, cx = (bpos[0] + W // 2) * step, (bpos[1] + W // 2) * step
y0 = max(0, min(2048 - 512, cy - 256)); x0 = max(0, min(4096 - 512, cx - 256))
S = 384
a_z = np.array(Image.fromarray(A[y0:y0+512, x0:x0+512], mode="L").resize((S, S), Image.NEAREST))
b_z = np.array(Image.fromarray(B[y0:y0+512, x0:x0+512], mode="L").resize((S, S), Image.NEAREST))
gap = np.full((S, 8), 70, dtype=np.uint8)
save_png(Image.fromarray(np.concatenate([a_z, gap, b_z], axis=1), mode="L"),
         "coast_before_after.png")
P("海岸窗口 crop y=%d x=%d（左=改造前，右=改造后）" % (y0, x0))

# ---- 3) 海面剖面图：规格锚点 vs 实测 ----
Wc, Hc = 980, 470
img = Image.new("RGB", (Wc, Hc), (255, 255, 255))
dr = ImageDraw.Draw(img)
L, R, T, Bm = 70, Wc - 150, 40, Hc - 50
def XY(r, v):
    x = L + (R - L) * r / 46.0
    y = Bm - (Bm - T) * (v - 8.0) / (94.0 - 8.0)
    return x, y
# 网格
for v in range(10, 95, 10):
    x0, y0_ = XY(0, v); x1, y1_ = XY(46, v)
    dr.line([x0, y0_, x1, y1_], fill=(228, 228, 228))
    dr.text((16, y0_ - 6), "%3d" % v, fill=(90, 90, 90))
for r in range(0, 47, 5):
    x0, y0_ = XY(r, 94); x1, y1_ = XY(r, 8)
    dr.line([x0, y0_, x1, y1_], fill=(240, 240, 240))
    dr.text((x0 - 8, Bm + 8), "%d" % r, fill=(90, 90, 90))
dr.line([L, T, L, Bm], fill=(60, 60, 60)); dr.line([L, Bm, R, Bm], fill=(60, 60, 60))
dr.text((Wc - 150, 60), "gray", fill=(40, 40, 40))
dr.text((R + 6, Bm + 20), "distance d (px)", fill=(40, 40, 40))
# 规格曲线
spec_r = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20,
          22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 41, 42, 44, 46]
def spec_v(d):
    if d <= 1: return 92.0
    if d <= 2: return 92 + (90 - 92) * (d - 1)
    if d <= 5: return 90 + (70 - 90) * (d - 2) / 3.0
    if d <= 10: return 70 + (50 - 70) * (d - 5) / 5.0
    if d <= 20: return 50 + (30 - 50) * (d - 10) / 10.0
    t = min(1.0, (d - 20) / 20.0)
    return max(10.0, 20 * t * t - 40 * t + 30)
pts = [XY(r, spec_v(r)) for r in spec_r]
dr.line(pts, fill=(200, 60, 60), width=3)
# 实测点（精确欧氏距离上的唯一值）
meas = {}
for r in range(1, 41):
    m = np.abs(d_sea - r) < 1e-3
    if m.sum():
        u = np.unique(B[m])
        meas[r] = (float(u[0]), int(m.sum()))
for r, (v, n) in meas.items():
    x, y = XY(r, v)
    dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(40, 90, 200))
# 关键锚点标注
for r, v in [(1, 92), (2, 90), (5, 70), (10, 50), (20, 30)]:
    x, y = XY(r, v)
    dr.text((x + 5, y - 16), "d=%d:%d" % (r, v), fill=(160, 30, 30))
save_png(img, "sea_profile.png")

# ---- 控制台/报告数据 ----
P("")
P("海面实测（精确欧氏距离，取唯一值）:")
for r in (1, 2, 3, 4, 5, 8, 10, 15, 20, 25, 30, 35, 40):
    if r in meas:
        P("   d=%-3d 实测=%3d  n=%d" % (r, int(meas[r][0]), meas[r][1]))
P("")
P("海面灰度是否单一值（同圈唯一）: %s" % all(len(np.unique(B[np.abs(d_sea - r) < 1e-3])) == 1 for r in meas))
dl = np.abs(B[1:, :].astype(np.int16) - B[:-1, :].astype(np.int16))
dh = np.abs(B[:, 1:].astype(np.int16) - B[:, :-1].astype(np.int16))
P("改造后相邻落差 max = %d" % max(dl.max(), dh.max()))
P("改造前相邻落差 max = %d"
  % max(np.abs(A[1:, :].astype(np.int16) - A[:-1, :].astype(np.int16)).max(),
        np.abs(A[:, 1:].astype(np.int16) - A[:, :-1].astype(np.int16)).max()))
P("陆地 %d..%d  海面 %d..%d" % (B[land].min(), B[land].max(), B[sea].min(), B[sea].max()))
P("输出目录: %s" % OUT)

io.open(os.path.join(OUT, "preview_report.txt"), "w", encoding="utf-8").write("\n".join(rep))
print("\n".join(rep))

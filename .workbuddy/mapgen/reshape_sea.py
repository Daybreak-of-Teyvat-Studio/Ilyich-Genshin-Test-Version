# -*- coding: utf-8 -*-
"""
只重算 heightmap 的海面梯度，陆地像素逐字节保持不变。

用户 2026-09-24 第二轮规格：
  灰度 10 = 最低，94 = 海平面。
  与陆地相接的海面 = 92；d=2 -> 90，d=5 -> 70，d=10 -> 50，d=20 -> 30；
  d=20 处斜率 -2/px，按三次 Hermite 平滑收到 d=40 -> 10，此后恒 10。
  陆地：全部 >= 96，沿海陆地（d_land==1）= 96，向内陆平滑。

用法: python reshape_sea.py [--in=<bmp>] [--out=<bmp>]
"""
import os, io, time, struct, shutil, glob
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
HM_DEF = os.path.join(G, "map", "heightmap.bmp")

_arg = lambda k, d: ([x for x in __import__("sys").argv if x.startswith(k)] or [None])[0]
HM = (_arg("--in=", None) or HM_DEF)[5:] if _arg("--in=", None) else HM_DEF
OUT = (_arg("--out=", None) or os.path.join(G, "map", "heightmap_v3.bmp"))[6:]

# ---- 规格参数 ----
LAND_TH = 94            # 海陆分界（海面 max 92、陆地 min 96，中间空档）
LAND_MIN = 96
RIM_SEA = 92
SEA_R = [1.0, 2.0, 5.0, 10.0, 20.0]
SEA_V = [92.0, 90.0, 70.0, 50.0, 30.0]
TAIL_END = 40.0         # d=20 处斜率 -2/px，Hermite 平滑收到 d=40 -> 10
SEA_FLOOR = 10.0

RUN = time.strftime("%m%d_%H%M%S")
APPDIR = os.path.join(G, ".workbuddy", "heightmap_sea", "run_" + RUN)
os.makedirs(APPDIR, exist_ok=True)

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

def save_png(img, path):
    try:
        img.save(path); return path
    except (PermissionError, OSError):
        alt = path[:-4] + "_%s.png" % time.strftime("%H%M%S")
        img.save(alt); return alt

def sea_profile(d):
    near = np.interp(d, SEA_R, SEA_V, left=SEA_V[0])
    t = np.clip((d - SEA_R[-1]) / (TAIL_END - SEA_R[-1]), 0.0, 1.0)
    tail = 20.0 * t * t - 40.0 * t + 30.0     # 端点值与斜率都与近岸段相接
    return np.maximum(np.where(d <= SEA_R[-1], near, tail), SEA_FLOOR)

t0 = time.time()
P("=" * 74)
P("heightmap 海面重塑（陆地不动）")
P("=" * 74)
P("输入: %s" % HM)
P("输出: %s" % OUT)
P("规格: 贴岸 %d；" % RIM_SEA + "；".join("d=%.0f -> %.0f" % (r, v) for r, v in zip(SEA_R[1:], SEA_V[1:]))
  + "；d=%.0f 处平滑收到 %.0f" % (TAIL_END, SEA_FLOOR))

raw = open(HM, "rb").read()
hdrsize, w, h, planes, bpp, comp, imgsize = struct.unpack("<IiiHHII", raw[14:38])
dataoff = struct.unpack("<I", raw[10:14])[0]
P("BMP: w=%d h=%d bpp=%d comp=%d dataoff=%d size=%d" % (w, h, bpp, comp, dataoff, len(raw)))

arr = np.array(Image.open(HM))
assert arr.shape == (abs(h), w), (arr.shape, (abs(h), w))
land = arr >= LAND_TH
sea = ~land
P("")
P("陆地 %d px  海洋 %d px" % (int(land.sum()), int(sea.sum())))
P("原图: 陆地 min=%d max=%d mean=%.2f | 海面 min=%d max=%d"
  % (int(arr[land].min()), int(arr[land].max()), arr[land].mean(),
     int(arr[sea].min()), int(arr[sea].max())))

d_sea = ndi.distance_transform_edt(sea).astype(np.float64)
d_land = ndi.distance_transform_edt(land).astype(np.float64)
new_sea_val = sea_profile(d_sea)
P("海面距离场 max = %.1f px" % d_sea.max())

# ---------- 合成：只换海面 ----------
out = arr.copy()
out[sea] = np.clip(np.rint(new_sea_val[sea]), 0, 255).astype(np.uint8)
out[sea] = np.minimum(out[sea], RIM_SEA)
out[land] = np.maximum(out[land], LAND_MIN)

# ---------- 校验 ----------
P("")
P("-" * 74); P("校验"); P("-" * 74)
P("陆地逐像素未变: %s" % bool((out[land] == arr[land]).all()))
P("陆地: min=%d max=%d  低于 %d 的像素 = %d"
  % (int(out[land].min()), int(out[land].max()), LAND_MIN, int((out[land] < LAND_MIN).sum())))
rim = out[d_land == 1]
P("沿海陆地(d_land==1): %d px, min=%d max=%d, 全部==%d: %s"
  % (rim.size, int(rim.min()), int(rim.max()), LAND_MIN, bool((rim == LAND_MIN).all())))
sv = out[sea]
P("海面: min=%d max=%d  高于 %d 的像素 = %d" % (int(sv.min()), int(sv.max()), RIM_SEA, int((sv > RIM_SEA).sum())))
g_v = np.abs(out[1:, :].astype(np.int16) - out[:-1, :].astype(np.int16))
g_h = np.abs(out[:, 1:].astype(np.int16) - out[:, :-1].astype(np.int16))
vpair = land[1:, :] ^ land[:-1, :]
hpair = land[:, 1:] ^ land[:, :-1]
print_v = np.unique(np.concatenate([g_v[vpair].ravel(), g_h[hpair].ravel()]))
P("海陆相邻对的落差取值集合 = %s" % print_v.tolist())

P("")
P("海面按距岸整数圈 r 的实测灰度（对照规格）:")
dsel = d_sea[sea]; vsel = out[sea].astype(np.float64)
for r in range(1, 41):
    m = (np.floor(dsel) == r) if r < 40 else (dsel >= 40)
    if m.sum() == 0:
        P("   r=%-3d  无像素" % r); continue
    exact = sea_profile(np.array([float(r)]))[0]
    P("   r=%-3d  n=%-8d  规格=%-4.1f  实测 median=%5.1f mean=%5.2f min=%d max=%d  |Δmedian|=%.2f"
      % (r, int(m.sum()), exact, np.median(vsel[m]), vsel[m].mean(),
         int(vsel[m].min()), int(vsel[m].max()), abs(exact - np.median(vsel[m]))))

P("")
P("海面改动统计:")
ch = (out != arr) & sea
P("   改动像素 %d (占海面 %.2f%%)" % (int(ch.sum()), 100.0 * ch.sum() / sea.sum()))
if ch.sum():
    dl = out[ch].astype(int) - arr[ch].astype(int)
    P("   灰度变化 min=%d max=%d mean=%.2f" % (int(dl.min()), int(dl.max()), dl.mean()))
    P("   按距岸圈统计变化量:")
    for r in (1, 2, 3, 5, 8, 10, 15, 20, 25, 30, 40):
        m = (np.floor(d_sea) == r) if r < 40 else (d_sea >= 40)
        m = m & ch
        if m.sum() == 0:
            P("     r=%-3d 无改动" % r); continue
        dd = out[m].astype(int) - arr[m].astype(int)
        P("     r=%-3d n=%-7d  Δ min=%d max=%d mean=%.2f" % (r, int(m.sum()), int(dd.min()), int(dd.max()), dd.mean()))

P("")
P("相邻像素落差: 纵向 max=%d 横向 max=%d" % (int(g_v.max()), int(g_h.max())))
both = np.concatenate([g_v.ravel(), g_h.ravel()])
for th in (1, 2, 3, 5, 8, 16):
    P("   |Δ| >= %-3d : %d 对" % (th, int((both >= th).sum())))

h_out = np.bincount(out.ravel(), minlength=256)
P("")
P("直方图: 非零灰阶 %d 个, 范围 %d..%d" % (int((h_out > 0).sum()), int(np.nonzero(h_out)[0].min()), int(np.nonzero(h_out)[0].max())))
P("   10:%-9d 30:%-8d 50:%-8d 70:%-8d 90:%-8d 92:%-8d 96:%-8d"
  % (h_out[10], h_out[30], h_out[50], h_out[70], h_out[90], h_out[92], h_out[96]))

# ---------- 预览 ----------
save_png(Image.fromarray(out, mode="L"), os.path.join(APPDIR, "preview_full.png"))
# 海陆各半的窗口，做 1:1 前后对比
step = 64
ch_, cw_ = 2048 // step, 4096 // step
cell_land = land[:ch_*step, :cw_*step].reshape(ch_, step, cw_, step).mean(axis=(1, 3))
W = 8; best, bpos = -1, (0, 0)
for i in range(0, ch_ - W):
    for j in range(0, cw_ - W):
        blk = cell_land[i:i+W, j:j+W]; frac = blk.mean()
        if 0.30 < frac < 0.75:
            score = blk.max() - blk.min()
            if score > best: best, bpos = score, (i, j)
cy, cx = (bpos[0] + W // 2) * step, (bpos[1] + W // 2) * step
y0 = max(0, min(2048 - 512, cy - 256)); x0 = max(0, min(4096 - 512, cx - 256))
a_ = np.array(Image.fromarray(arr[y0:y0+512, x0:x0+512], mode="L").resize((768, 768), Image.NEAREST))
b_ = np.array(Image.fromarray(out[y0:y0+512, x0:x0+512], mode="L").resize((768, 768), Image.NEAREST))
sep = np.full((768, 6), 40, dtype=np.uint8)
cmp_ = np.concatenate([a_, sep, b_], axis=1)
save_png(Image.fromarray(cmp_, mode="L"), os.path.join(APPDIR, "coast_before_after.png"))
save_png(Image.fromarray(b_, mode="L"), os.path.join(APPDIR, "coast_after.png"))
P("")
P("预览: preview_full.png / coast_before_after.png (crop y=%d x=%d, 1.5x)" % (y0, x0))

# ---------- 落盘 ----------
bk = os.path.join(G, ".workbuddy", "backup_20260924_heightmap")
os.makedirs(bk, exist_ok=True)
dst = os.path.join(bk, "heightmap_presea_%s.bmp" % time.strftime("%Y%m%d_%H%M%S"))
shutil.copy2(HM, dst)
P("已备份当前 heightmap -> %s (%d bytes)" % (dst, os.path.getsize(dst)))

body = out[::-1, :].tobytes()
assert len(body) == abs(h) * w * (bpp // 8), (len(body), abs(h) * w * (bpp // 8))
blob = bytearray(raw[:dataoff] + body)
struct.pack_into("<I", blob, 2, len(blob))
struct.pack_into("<I", blob, 34, len(body))
with open(OUT, "wb") as f:
    f.write(bytes(blob))
P("已写出 %s (%d bytes)" % (OUT, os.path.getsize(OUT)))

chk = np.array(Image.open(OUT))
P("回读校验: 与内存结果逐像素一致 = %s" % bool((chk == out).all()))
P("")
P("耗时 %.1f s" % (time.time() - t0))

with io.open(os.path.join(APPDIR, "report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep))
np.save(os.path.join(APPDIR, "result.npy"), out)
print("DONE -> %s" % APPDIR)

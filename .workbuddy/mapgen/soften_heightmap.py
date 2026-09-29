# -*- coding: utf-8 -*-
"""
柔化 heightmap：构建海面距离梯度 + 陆地沿海 96 的平台与平滑过渡。

规则（用户 2026-09-24 第二轮规格）：
  灰度 10 = 最低，94 = 海平面，255 = 最高峰。
  与陆地相接的海面 = 92；之后 2px -> 90，5px -> 70，10px -> 50，20px -> 30；
  d=20 处斜率 -2/px，按三次 Hermite 平滑收到 40px -> 10（最低），此后恒为 10。
  所有陆地 >= 96，沿海陆地 = 96，向内陆平滑抬升。
  （第一轮规格 1px->90 / 6px->70 / 11px->50 / 21px->30 已废弃。）

用法：
  python soften_heightmap.py                       # 试算：只出报告与预览，不写盘
  python soften_heightmap.py --apply --out=<bmp>   # 落盘到新文件（先自动备份当前 heightmap）
  可调：--in= --out= --sea_r=1,2,5,10,20 --sea_v=92,90,70,50,30 --tail=40 --sig=2.0 --ramp=12
"""
import os, io, sys, glob, shutil, struct, time
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
HM_DEFAULT = os.path.join(GAMMA, "map", "heightmap.bmp")
OUTDIR = os.path.join(GAMMA, ".workbuddy", "mapgen")
APPDIR = os.path.join(GAMMA, ".workbuddy", "heightmap_soft", "run_" + time.strftime("%m%d_%H%M%S"))
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(APPDIR, exist_ok=True)

APPLY = "--apply" in sys.argv
_INARG = [x for x in sys.argv if x.startswith("--in=")]
_OUTARG = [x for x in sys.argv if x.startswith("--out=")]
# 输入务必是「未柔化的原图」，否则会二次柔化（峰高会平白掉几个灰阶）
HM = _INARG[0][5:] if _INARG else HM_DEFAULT
OUT = _OUTARG[0][6:] if _OUTARG else HM_DEFAULT
INPLACE = os.path.normcase(os.path.abspath(OUT)) == os.path.normcase(os.path.abspath(HM_DEFAULT))

def _numarg(key, default):
    for x in sys.argv:
        if x.startswith(key):
            return float(x[len(key):])
    return default

def _listarg(key, default):
    for x in sys.argv:
        if x.startswith(key):
            return [float(v) for v in x[len(key):].split(",")]
    return default

# ---- 可调参数 ----
LAND_MIN = 96          # 陆地最低灰度
SEA_LEVEL = 94         # 海平面
RIM_SEA = 92           # 与陆地相接的海面。硬性约束：所有海洋像素 <= 92（对照 DOT MAP 3.0 的黑色区域）
SEA_R_NEAR = _listarg("--sea_r=", [1.0, 2.0, 5.0, 10.0, 20.0])      # 距岸像素数（用户给定锚点）
SEA_V_NEAR = _listarg("--sea_v=", [92.0, 90.0, 70.0, 50.0, 30.0])   # 对应灰度
SEA_FLOOR = 10.0       # 最低灰度
SEA_TAIL_END = _numarg("--tail=", 40.0)   # 末锚点处斜率与近岸段相接，平滑收到此处斜率归零、值为 10
RAMP = _numarg("--ramp=", 12.0)    # 陆地沿海平台向内陆抬升的像素跨度
SIG = _numarg("--sig=", 2.0)       # 陆地高程高斯柔化 sigma（扫描后取 2.0）
KEEPMAX = "--keepmax" in sys.argv  # 柔化后把峰高补回原值（单调线性重标定，沿海 96 不变）


def sea_profile(d):
    """海面灰度 = f(到最近陆地的欧氏距离)。近岸严格走用户锚点，远端按 Hermite 平滑入底。"""
    v_near = np.interp(d, SEA_R_NEAR, SEA_V_NEAR, left=SEA_V_NEAR[0])
    r0, v0 = SEA_R_NEAR[-1], SEA_V_NEAR[-1]
    span = SEA_TAIL_END - r0
    m0 = (SEA_V_NEAR[-1] - SEA_V_NEAR[-2]) / (SEA_R_NEAR[-1] - SEA_R_NEAR[-2])   # 与近岸段斜率相接
    t = np.clip((d - r0) / span, 0.0, 1.0)
    v_tail = ((2.0*t**3 - 3.0*t**2 + 1.0) * v0
              + (t**3 - 2.0*t**2 + t) * span * m0
              + (-2.0*t**3 + 3.0*t**2) * SEA_FLOOR)
    return np.maximum(np.where(d <= r0, v_near, v_tail), SEA_FLOOR)

rep = []
def P(*a):
    s = " ".join(str(x) for x in a)
    rep.append(s)


def save_png(img, path):
    """预览图可能被预览面板占用 → 写入失败时降级到带时间戳的新文件名，绝不中断主流程。"""
    try:
        img.save(path)
        return path
    except (PermissionError, OSError):
        alt = path[:-4] + "_%s.png" % time.strftime("%H%M%S")
        img.save(alt)
        return alt

t0 = time.time()
P("=" * 78)
P("heightmap 柔化   apply=%s" % APPLY)
P("=" * 78)

# ---------- 读原图（含原始头与调色板，写回时逐字节沿用） ----------
raw = open(HM, "rb").read()
hdrsize, w, h, planes, bpp, comp, imgsize = struct.unpack("<IiiHHII", raw[14:38])
dataoff = struct.unpack("<I", raw[10:14])[0]
P("原始 BMP: w=%d h=%d bpp=%d comp=%d dataoff=%d size=%d" % (w, h, bpp, comp, dataoff, len(raw)))
P("biHeight=%d (%s)" % (h, "bottom-up" if h > 0 else "top-down"))

arr = np.array(Image.open(HM))
assert arr.shape == (abs(h), w), arr.shape
P("读入阵列 %s dtype=%s" % (arr.shape, arr.dtype))

land = arr >= 94
sea = ~land
P("陆地 %d px (%.3f%%)  海洋 %d px" % (land.sum(), 100.0*land.sum()/land.size, sea.sum()))
P("原陆地灰度 min=%d max=%d mean=%.2f" % (arr[land].min(), arr[land].max(), arr[land].mean()))

# ---------- 掩膜健康度（只报告，不改动） ----------
lbl, nlab = ndi.label(land, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
sz = np.bincount(lbl.ravel())[1:]
P("陆地连通块 %d 个：1px=%d  2-4px=%d  5-20px=%d  21-100px=%d  >100px=%d"
  % (nlab, (sz==1).sum(), ((sz>=2)&(sz<=4)).sum(), ((sz>=5)&(sz<=20)).sum(),
     ((sz>=21)&(sz<=100)).sum(), (sz>100).sum()))
P("最大 8 块像素数: %s" % [int(x) for x in np.sort(sz)[::-1][:8]])

# ---------- 海洋：到最近陆地的欧氏距离 -> 分段灰度 ----------
d_sea = ndi.distance_transform_edt(sea).astype(np.float64)
P("")
P("海面距离场: max=%.1f px" % d_sea.max())
sea_val = sea_profile(d_sea)
P("海面剖面锚点: r=%s -> %s ；r=%.0f 处平滑收到 %d" % (SEA_R_NEAR, SEA_V_NEAR, SEA_TAIL_END, int(SEA_FLOOR)))

# ---------- 陆地：掩膜内高斯柔化 + 沿海平台 ----------
d_land = ndi.distance_transform_edt(land).astype(np.float64)
num = ndi.gaussian_filter(np.where(land, arr.astype(np.float64), 0.0), SIG)
den = ndi.gaussian_filter(land.astype(np.float64), SIG)
blur = np.divide(num, np.maximum(den, 1e-9))
t = np.clip((d_land - 1.0) / (RAMP - 1.0), 0.0, 1.0)
sm = t * t * (3.0 - 2.0 * t)
land_val = LAND_MIN + sm * (blur - LAND_MIN)

# 可选：把柔化损失掉的峰高补回去。单调线性重标定，d_land==1 处 sm=0 故 96 保持 96。
if KEEPMAX:
    _lm = float(land_val[land].max()); _om = float(arr[land].max())
    if _lm > LAND_MIN:
        land_val = LAND_MIN + (land_val - LAND_MIN) * (_om - LAND_MIN) / (_lm - LAND_MIN)
        P("--keepmax：陆地重标定 %.1f -> %.1f（比例 %.4f）" % (_lm, _om, (_om - LAND_MIN) / (_lm - LAND_MIN)))

# ---------- 合成 ----------
out = np.where(land, land_val, sea_val)
out = np.clip(np.rint(out), 10, 255).astype(np.uint8)
out[land] = np.maximum(out[land], LAND_MIN)          # 陆地 >= 96
out[~land] = np.minimum(out[~land], RIM_SEA)         # 海面 <= 92（硬性上限）

# ---------- 校验 ----------
P("")
P("-" * 78)
P("校验")
P("-" * 78)
lv = out[land]; sv = out[sea]
P("陆地: min=%d max=%d mean=%.2f  | 低于 96 的像素 = %d" % (lv.min(), lv.max(), lv.mean(), int((lv < LAND_MIN).sum())))
rim = out[d_land == 1]
P("沿海陆地(d==1): 像素 %d 个, min=%d max=%d, 全部==96: %s"
  % (rim.size, rim.min(), rim.max(), bool((rim == LAND_MIN).all())))
P("海面: min=%d max=%d  | 高于 %d 的像素 = %d" % (sv.min(), sv.max(), RIM_SEA, int((sv > RIM_SEA).sum())))

P("")
P("对照 .workbuddy\\DOT MAP 3.0.bmp（紫=陆地 #9644C0，黑=海洋 #051412）:")
REF = os.path.join(GAMMA, ".workbuddy", "DOT MAP 3.0.bmp")
if os.path.isfile(REF):
    _r = np.array(Image.open(REF))
    ref_land = (_r[:, :, 0] == 150) & (_r[:, :, 1] == 68) & (_r[:, :, 2] == 192)
    ref_sea = ~ref_land
    P("   参照图: 陆地 %d px  海洋 %d px" % (ref_land.sum(), ref_sea.sum()))
    P("   掩膜与参照图逐像素一致: %s" % bool((ref_land == land).all()))
    P("   参照图'海洋'像素中灰度 > %d 的: %d" % (RIM_SEA, int((out[ref_sea] > RIM_SEA).sum())))
    P("   参照图'陆地'像素中灰度 < %d 的: %d" % (LAND_MIN, int((out[ref_land] < LAND_MIN).sum())))
else:
    P("   未找到参照图，跳过")

P("")
P("海面按距岸整数圈的中位灰度（对照用户规格）:")
dsel = d_sea[sea]
vsel = out[sea].astype(np.float64)
for r in range(1, 33):
    m = (np.floor(dsel) == r) if r < 32 else (dsel >= 32)
    if m.sum() == 0:
        P("   r=%-3d  无像素" % r); continue
    P("   r=%-3d  n=%-8d  median=%5.1f  mean=%5.2f  min=%d max=%d"
      % (r, int(m.sum()), np.median(vsel[m]), vsel[m].mean(), int(vsel[m].min()), int(vsel[m].max())))

P("")
P("锚点精确校验（np.abs(d-r)<1e-3，即真正落在该欧氏距离上的像素；按 floor 分桶会把中位数拉低约 1）:")
for r, v in zip(SEA_R_NEAR, SEA_V_NEAR):
    m = np.abs(d_sea - r) < 1e-3
    if m.sum() == 0:
        P("   d=%-4.0f  无像素" % r); continue
    vv = out[m].astype(np.float64)
    P("   d=%-4.0f 规格=%5.1f  n=%-7d  mean=%6.3f  median=%5.1f  min=%d max=%d  |mean-规格|=%.3f"
      % (r, v, int(m.sum()), vv.mean(), np.median(vv), int(vv.min()), int(vv.max()), abs(vv.mean() - v)))

# 远端收尾：斜率应单调趋零，不该出现折角
_r = np.arange(1.0, SEA_TAIL_END + 8.0, 1.0)
_v = sea_profile(_r)
_sl = np.diff(_v)
P("   远端斜率(每 px): %s" % " ".join("%.2f" % s for s in _sl[:int(SEA_TAIL_END) + 4]))
P("   收尾末段最大斜率 = %.3f（应趋近 0）" % float(np.abs(_sl[int(SEA_TAIL_END) - 2:]).max()))

# 相邻像素最大落差
def maxgap(a, axis, shift_axis_len):
    d1 = np.abs(a[1:, :].astype(np.int16) - a[:-1, :].astype(np.int16))
    d2 = np.abs(a[:, 1:].astype(np.int16) - a[:, :-1].astype(np.int16))
    return d1, d2
g_v, g_h = maxgap(out, 0, None)
P("")
P("相邻像素落差: 纵向 max=%d  横向 max=%d" % (g_v.max(), g_h.max()))
both = np.concatenate([g_v.ravel(), g_h.ravel()])
for th in [1, 2, 3, 5, 8, 16]:
    P("   |Δ| >= %-3d : %d 对" % (th, int((both >= th).sum())))
# 落差大于 3 的位置应只在海岸线上（陆地<->海面）
big = np.zeros_like(out, dtype=bool)
big[1:, :] |= (g_v > 3); big[:-1, :] |= (g_v > 3)
big[:, 1:] |= (g_h > 3); big[:, :-1] |= (g_h > 3)
near_coast = ndi.binary_dilation(land, iterations=1) & ndi.binary_dilation(sea, iterations=1)
off = big & ~ndi.binary_dilation(near_coast, iterations=1)
P("   |Δ|>3 且不在海岸线的像素: %d  |  与陆地相邻海面在 r>1 处落差>3 的: %d"
  % (int(off.sum()), int((((out[:, :-1] != out[:, 1:]) & (np.abs(out[:,1:].astype(int)-out[:,:-1].astype(int))>3) & sea[:,1:] & sea[:,:-1])).sum())))

# 直方图
h_out = np.bincount(out.ravel(), minlength=256)
P("")
P("输出直方图（非零）: 共 %d 个灰阶, 10..%d" % (int((h_out > 0).sum()), int(np.nonzero(h_out)[0].max())))
P("   10:%-9d 30:%-8d 50:%-8d 70:%-8d 90:%-8d 93:%-8d 96:%-8d 97:%-8d"
  % (h_out[10], h_out[30], h_out[50], h_out[70], h_out[90], h_out[93], h_out[96], h_out[97]))

# ---------- 预览图 ----------
_p1 = save_png(Image.fromarray(out, mode="L"), os.path.join(APPDIR, "preview_full.png"))
# 找一块海陆各半且靠近山地的窗口做 1:1 放大
step = 64
cell_land = land[:2048//step*step, :4096//step*step].reshape(2048//step, step, 4096//step, step).mean(axis=(1,3))
cell_hi = out[:2048//step*step, :4096//step*step].reshape(2048//step, step, 4096//step, step).max(axis=(1,3))
ch, cw = cell_land.shape
best, bpos = -1, (0, 0)
W = 8
for i in range(0, ch - W):
    for j in range(0, cw - W):
        blk = cell_land[i:i+W, j:j+W]
        frac = blk.mean()
        if 0.30 < frac < 0.75:
            score = blk.max() - blk.min() + cell_hi[i:i+W, j:j+W].max() / 100.0
            if score > best:
                best, bpos = score, (i, j)
cy, cx = (bpos[0] + W//2) * step, (bpos[1] + W//2) * step
y0 = max(0, min(2048 - 512, cy - 256)); x0 = max(0, min(4096 - 512, cx - 256))
_p2 = save_png(Image.fromarray(out[y0:y0+512, x0:x0+512], mode="L").resize((1024, 1024), Image.NEAREST),
               os.path.join(APPDIR, "preview_coast_zoom.png"))
P("")
P("预览: %s ；%s（crop y=%d x=%d, 2x 放大）" % (os.path.basename(_p1), os.path.basename(_p2), y0, x0))

# ---------- 落盘 ----------
if APPLY:
    if INPLACE:
        bk = os.path.join(GAMMA, ".workbuddy", "backup_20260924_heightmap")
        os.makedirs(bk, exist_ok=True)
        is_first = not glob.glob(os.path.join(bk, "heightmap_orig_*.bmp"))
        dst = os.path.join(bk, "heightmap_%s_%s.bmp"
                           % ("orig" if is_first else "prev", time.strftime("%Y%m%d_%H%M%S")))
        try:
            shutil.copy2(HM, dst)
            P("")
            P("已备份%s -> %s (%d bytes)" % ("原始文件" if is_first else "上一版", dst, os.path.getsize(dst)))
        except Exception as e:
            P("")
            P("！！备份失败（%s），中止就地写入" % type(e).__name__)
            raise SystemExit(2)
    # 逐字节沿用原文件头与调色板，仅替换像素数据
    body = out[::-1, :].tobytes()          # BMP 行自下而上
    assert len(body) == abs(h) * w * (bpp // 8), (len(body), abs(h)*w*(bpp//8))
    blob = bytearray(raw[:dataoff] + body)
    struct.pack_into("<I", blob, 2, len(blob))          # bfSize
    struct.pack_into("<I", blob, 34, len(body))         # biSizeImage
    try:
        with open(OUT, "wb") as f:
            f.write(bytes(blob))
        wrote = OUT
    except (PermissionError, OSError) as e:
        wrote = OUT[:-4] + "_new.bmp"
        with open(wrote, "wb") as f:
            f.write(bytes(blob))
        P("")
        P("！！目标被拒写（%s），已改写到 %s" % (type(e).__name__, wrote))
    P("已写入 %s (%d bytes)" % (wrote, os.path.getsize(wrote)))
    if INPLACE:
        try:
            shutil.copy2(OUT, os.path.join(GAMMA, ".workbuddy", "heightmap.bmp"))
            P("已同步 .workbuddy\\heightmap.bmp")
        except Exception as e:
            P("同步 .workbuddy\\heightmap.bmp 失败: %s（该副本可能已过期）" % type(e).__name__)
else:
    P("")
    P("（试算模式，未写盘）")

P("")
P("耗时 %.1f s" % (time.time() - t0))

with io.open(os.path.join(APPDIR, "report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep))
with io.open(os.path.join(APPDIR, "result.npy"), "wb") as f:
    np.save(f, out)
print("\n".join(rep))

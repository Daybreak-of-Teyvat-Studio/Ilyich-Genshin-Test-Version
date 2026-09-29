# -*- coding: utf-8 -*-
"""按 heightmap 高度阈值把 terrain 对应处涂成山地色，输出到新文件（不改动原 terrain.bmp）
用法:  python paint_terrain_mountain.py --out=<路径> [--th=175] [--minpix=0]
"""
import os, io, sys, shutil, struct, time
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
M = os.path.join(G, "map")
H = os.path.join(G, ".workbuddy")
HM = os.path.join(M, "heightmap.bmp")
TB = os.path.join(M, "terrain.bmp")
BKD = os.path.join(H, "backup_20260924_terrain")

_out = [x for x in sys.argv if x.startswith("--out=")]
OUT = _out[0][6:] if _out else os.path.join(M, "terrain_mountain.bmp")
_th = [x for x in sys.argv if x.startswith("--th=")]
TH = int(_th[0][5:]) if _th else 175
_mp = [x for x in sys.argv if x.startswith("--minpix=")]
MINPIX = int(_mp[0][9:]) if _mp else 0
_c = [x for x in sys.argv if x.startswith("--color=")]
COLOR = tuple(int(v) for v in _c[0][8:].split(",")) if _c else (243, 199, 147)
# 默认 (243,199,147) = 原版 terrain.bmp 调色板索引 31 = desert_mountain_tops (type = mountain)
# 其他山地系调色板色: (58,131,82)=idx20 mountain_variation_grass, (255,255,255)=idx16 snow_16

rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

P("heightmap : %s (%s)" % (HM, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(HM)))))
P("terrain 源: %s (%s)" % (TB, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(TB)))))
P("输出      : %s" % OUT)
P("阈值 = %d   目标色 = %s   最小块 = %d" % (TH, COLOR, MINPIX))
P("")

hm = np.array(Image.open(HM))
land = hm >= 94
mask = land & (hm >= TH)
P("陆地 %d px；命中(>=%d) = %d px (占陆地 %.2f%%)；命中区高度 %d..%d"
  % (int(land.sum()), TH, int(mask.sum()), 100.0 * mask.sum() / land.sum(),
     int(hm[mask].min()), int(hm[mask].max())))

lab, n = ndi.label(mask, structure=np.ones((3, 3)))
sizes = np.bincount(lab.ravel())[1:]
P("连通块 %d 个，最大 %d px，前 10: %s" % (n, int(sizes.max()), sorted(sizes.tolist(), reverse=True)[:10]))
if MINPIX > 1:
    keep = np.isin(lab, np.where(sizes >= MINPIX)[0] + 1)
    mask = mask & keep
    lab, n = ndi.label(mask, structure=np.ones((3, 3)))
    sizes = np.bincount(lab.ravel())[1:]
    P("过滤 < %d px 后：块 %d 个，覆盖 %d px" % (MINPIX, n, int(mask.sum())))

tb = np.array(Image.open(TB))
out = tb.copy()
out[mask] = COLOR
sel = tb.reshape(-1, 3)[mask.ravel()]
uk, cnt = np.unique(sel, axis=0, return_counts=True)
P("被覆盖的原色: " + "  ".join("rgb(%d,%d,%d)=%d" % (r, g, b, c) for (r, g, b), c in zip(uk, cnt)))
P("涂色后该色像素数 = %d" % int(((out[:, :, 0] == COLOR[0]) & (out[:, :, 1] == COLOR[1]) & (out[:, :, 2] == COLOR[2])).sum()))

# 预览
RUN = time.strftime("%m%d_%H%M%S")
APPDIR = os.path.join(H, "terrain_paint_preview", "run_" + RUN)
os.makedirs(APPDIR, exist_ok=True)
sheet = Image.new("RGB", (1024, 512 * 2 + 8), (20, 20, 20))
sheet.paste(Image.fromarray(tb).resize((1024, 512), Image.NEAREST), (0, 0))
sheet.paste(Image.fromarray(out).resize((1024, 512), Image.NEAREST), (0, 520))
try:
    sheet.save(os.path.join(APPDIR, "before_after.png"))
except Exception as e:
    P("预览保存失败: %s" % e)
if n:
    big = int(np.argmax(sizes)) + 1
    ys, xs = np.where(lab == big)
    cy, cx = int(ys.mean()), int(xs.mean())
    h, w = hm.shape
    y0 = max(0, min(h - 320, cy - 160)); x0 = max(0, min(w - 320, cx - 160))
    z = Image.new("RGB", (320 * 2 + 6, 320), (20, 20, 20))
    z.paste(Image.fromarray(tb[y0:y0+320, x0:x0+320]), (0, 0))
    z.paste(Image.fromarray(out[y0:y0+320, x0:x0+320]), (326, 0))
    try:
        z.resize(((320 * 2 + 6) * 2, 640), Image.NEAREST).save(os.path.join(APPDIR, "zoom_largest.png"))
    except Exception as e:
        P("放大图保存失败: %s" % e)
    P("最大块 %d px 位于 y=%d x=%d" % (int(sizes.max()), cy, cx))

# 备份原 terrain（新建文件，允许）
os.makedirs(BKD, exist_ok=True)
bak = os.path.join(BKD, "terrain_orig_%s.bmp" % time.strftime("%Y%m%d_%H%M%S"))
if not os.path.isfile(bak):
    shutil.copy2(TB, bak)
    P("已备份原 terrain -> %s" % bak)

# 写出新文件（保留原 BMP 头 54 字节，仅换像素体）
raw = open(TB, "rb").read()
off = struct.unpack("<I", raw[10:14])[0]
body = out[::-1, :, ::-1].tobytes()      # 行自下而上 + RGB->BGR（BMP 24bit 为 BGR 存储）
assert len(body) == 4096 * 2048 * 3, len(body)
blob = bytearray(raw[:off] + body)
struct.pack_into("<I", blob, 2, len(blob))
struct.pack_into("<I", blob, 34, len(body))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(bytes(blob))
P("已写出 %s (%d bytes)" % (OUT, os.path.getsize(OUT)))

# 自校验
chk = np.array(Image.open(OUT))
P("回读校验: shape=%s  目标色像素=%d  与原图差异像素=%d"
  % (chk.shape, int(((chk[:, :, 0] == COLOR[0]) & (chk[:, :, 1] == COLOR[1]) & (chk[:, :, 2] == COLOR[2])).sum()),
     int((chk != tb).any(axis=2).sum())))
P("差异是否恰好等于 mask: %s" % bool(((chk != tb).any(axis=2) == mask).all()))
P("非命中区是否完全未变: %s" % bool((chk[~mask] == tb[~mask]).all()))

io.open(os.path.join(H, "terrain_paint_report_%s.txt" % RUN), "w", encoding="utf-8").write("\n".join(rep))
print("DONE")

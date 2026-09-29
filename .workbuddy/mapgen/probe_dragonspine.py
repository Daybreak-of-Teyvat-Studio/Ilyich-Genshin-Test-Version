# -*- coding: utf-8 -*-
"""探查龙脊雪山（DRA）所辖各州在地图上的像素范围与高度分布。
只读，不改任何 MOD 文件。结果写入 _probe_dragonspine.txt。
"""
import io, os, re
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
M = os.path.join(G, "map")
OUT = r"C:\Users\XIANGZIYUAN\hoi4lint\_probe_dragonspine.txt"

log = []
def P(*a):
    log.append(" ".join(str(x) for x in a))

DRA_STATES = [520, 521, 533, 534, 535, 547, 565]

# --- 1. definition.csv : 省 id -> 颜色 ---
id2rgb = {}
with io.open(os.path.join(M, "definition.csv"), "r", encoding="utf-8-sig", errors="replace") as f:
    for line in f:
        p = line.strip().split(";")
        if len(p) < 4:
            continue
        try:
            id2rgb[int(p[0])] = (int(p[1]), int(p[2]), int(p[3]))
        except ValueError:
            continue
P("definition.csv 省份数 = %d" % len(id2rgb))

# --- 2. provinces.bmp : 颜色 -> 省 id ---
prov = np.array(Image.open(os.path.join(M, "provinces.bmp")))
P("provinces.bmp shape=%s mode=%s" % (prov.shape, Image.open(os.path.join(M, "provinces.bmp")).mode))
packed = (prov[:, :, 0].astype(np.uint32) << 16) | (prov[:, :, 1].astype(np.uint32) << 8) | prov[:, :, 2].astype(np.uint32)
rgb2id = {(r << 16) | (g << 8) | b: pid for pid, (r, g, b) in id2rgb.items()}

hm = np.array(Image.open(os.path.join(M, "heightmap.bmp")))
P("heightmap shape=%s  min=%d max=%d" % (hm.shape, hm.min(), hm.max()))
P("")

# --- 3. 各州的省列表 ---
allprov = []
for sid in DRA_STATES:
    path = None
    for fn in os.listdir(os.path.join(G, "history", "states")):
        m = re.match(r"^(\d+)-", fn)
        if m and int(m.group(1)) == sid:
            path = os.path.join(G, "history", "states", fn)
            break
    if path is None:
        P("州 %d : 找不到文件" % sid)
        continue
    t = io.open(path, "r", encoding="utf-8-sig", errors="replace").read()
    t = re.sub(r"#[^\n]*", "", t)
    blk = re.search(r"provinces\s*=\s*\{([^}]*)\}", t)
    provs = [int(x) for x in re.findall(r"\d+", blk.group(1))] if blk else []
    allprov += provs
    name = re.search(r'name\s*=\s*"([^"]*)"', t)
    P("州 %-4d %-34s 省数 %3d" % (sid, name.group(1) if name else "?", len(provs)))

allprov = sorted(set(allprov))
P("")
P("DRA 合计省数 = %d" % len(allprov))

# --- 4. 掩膜 ---
mask = np.zeros(hm.shape, dtype=bool)
missing = []
for pid in allprov:
    c = id2rgb.get(pid)
    if c is None:
        missing.append(pid)
        continue
    key = (c[0] << 16) | (c[1] << 8) | c[2]
    mask |= (packed == key)
if missing:
    P("definition.csv 中缺失的省: %s" % missing[:20])

ys, xs = np.where(mask)
P("DRA 像素掩膜 = %d px" % int(mask.sum()))
if mask.sum():
    P("包围盒 y=%d..%d  x=%d..%d   质心 y=%d x=%d" % (ys.min(), ys.max(), xs.min(), xs.max(), int(ys.mean()), int(xs.mean())))
P("")

# --- 5. DRA 范围内高度分布 ---
if mask.sum():
    P("== DRA 范围内高度直方图 ==")
    for lo in range(90, 256, 5):
        n = int(((hm >= lo) & (hm < lo + 5) & mask).sum())
        if n:
            P("  %3d-%3d : %6d" % (lo, lo + 4, n))
    P("")
    P("== DRA 范围高段 ==")
    for t in (120, 125, 130, 140, 150, 160, 170, 180):
        P("  >=%3d : %6d" % (t, int((hm >= t) & mask).sum() if False else int(((hm >= t) & mask).sum())))
    P("  DRA 内最高 = %d" % int(hm[mask].max()))
    P("")

    P("== DRA 范围内 >=150 的连通块 ==")
    m2 = (hm >= 150) & mask
    lab, n = ndi.label(m2, np.ones((3, 3)))
    sz = np.bincount(lab.ravel())[1:]
    if n:
        for i in np.argsort(-sz)[:10]:
            yy, xx = np.where(lab == i + 1)
            P("  块 %6d px  y=%d..%d x=%d..%d  峰值 %d" % (sz[i], yy.min(), yy.max(), xx.min(), xx.max(), int(hm[lab == i + 1].max())))
    P("")

# --- 6. 全图与 DRA 的关系：全图高区是否就在 DRA ---
P("== 全图 >=150 的像素中有多少落在 DRA ==")
g150 = hm >= 150
P("  全图 >=150 : %d px；其中 DRA 内 %d px（%.1f%%）" % (int(g150.sum()), int((g150 & mask).sum()), 100.0 * int((g150 & mask).sum()) / max(1, int(g150.sum()))))

# --- 7. 蒙德大区：州号参考图目录里找 DRA 州号 ---
P("")
P("== 参考图 ==")
for d in ("分界图层", "划分结果"):
    p = os.path.join(G, "..", "Gamma_地图", d)
    if os.path.isdir(p):
        P("  %s: %s" % (d, sorted(os.listdir(p))[:20]))

io.open(OUT, "w", encoding="utf-8").write("\n".join(log))
print("done")

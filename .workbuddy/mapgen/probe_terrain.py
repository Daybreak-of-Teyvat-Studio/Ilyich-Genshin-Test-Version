# -*- coding: utf-8 -*-
"""探测 heightmap 与 terrain.bmp 的现状与格式"""
import os, io, sys, struct, time
import numpy as np
from PIL import Image

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
M = os.path.join(G, "map")
H = os.path.join(G, ".workbuddy")

rep = []
def P(*a):
    rep.append(" ".join(str(x) for x in a))

P("===== map/ 目录 =====")
for n in sorted(os.listdir(M)):
    p = os.path.join(M, n)
    if os.path.isfile(p):
        st = os.stat(p)
        P("  %-28s %10d  %s" % (n, st.st_size, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))))

def bmp_head(p):
    raw = open(p, "rb").read(60)
    sig = raw[:2].decode("latin1")
    fsz = struct.unpack("<I", raw[2:6])[0]
    off = struct.unpack("<I", raw[10:14])[0]
    hs, w, h, pl, bpp = struct.unpack("<IiiHH", raw[14:30])
    return dict(sig=sig, fsize=fsz, off=off, hdrsize=hs, w=w, h=h, pl=pl, bpp=bpp, real=os.path.getsize(p))

for name in ["heightmap.bmp", "terrain.bmp", "heightmap_new.bmp", "heightmap_new_new.bmp"]:
    p = os.path.join(M, name)
    P("")
    P("===== %s =====" % name)
    if not os.path.isfile(p):
        P("  MISSING")
        continue
    P("  head:", bmp_head(p))
    im = Image.open(p)
    P("  PIL mode=%s size=%s" % (im.mode, im.size))
    a = np.array(im)
    P("  array shape=%s dtype=%s" % (a.shape, a.dtype))
    if a.ndim == 2:
        u, c = np.unique(a, return_counts=True)
        P("  唯一灰度值 %d 个: min=%d max=%d" % (len(u), u.min(), u.max()))
        P("  灰度分布(每 10 一档):")
        hist = np.bincount(a.ravel(), minlength=256)
        line = []
        for lo in range(0, 256, 10):
            n = int(hist[lo:lo+10].sum())
            if n:
                line.append("%d-%d:%d" % (lo, lo+9, n))
        P("    " + "  ".join(line))
    else:
        # 彩色：统计唯一颜色
        flat = a.reshape(-1, a.shape[2])
        cols, cnt = np.unique(flat, axis=0, return_counts=True)
        P("  唯一颜色 %d 种，Top 20:" % len(cols))
        idx = np.argsort(-cnt)[:20]
        for i in idx:
            r, g, b = cols[i]
            P("    #%02X%02X%02X  rgb(%d,%d,%d)  %d px" % (r, g, b, r, g, b, cnt[i]))

# default.map 里的 terrain 定义
P("")
P("===== map/default.map (terrain 段) =====")
p = os.path.join(M, "default.map")
if os.path.isfile(p):
    t = io.open(p, "r", encoding="utf-8-sig", errors="replace").read()
    P(t)

out = os.path.join(H, "terrain_probe.txt")
io.open(out, "w", encoding="utf-8").write("\n".join(rep))
print("WROTE", out)

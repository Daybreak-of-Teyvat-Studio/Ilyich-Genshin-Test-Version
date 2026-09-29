# -*- coding: utf-8 -*-
import struct, os, collections
import numpy as np

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
VAN   = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\map"
OUT   = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\scripts\_diag3.txt"

def hdr(p):
    with open(p, "rb") as f:
        b = f.read(64)
    (off,) = struct.unpack_from("<I", b, 10)
    (hs,) = struct.unpack_from("<I", b, 14)
    w, h = struct.unpack_from("<ii", b, 18)
    planes, bpp = struct.unpack_from("<HH", b, 26)
    clrused = struct.unpack_from("<I", b, 46)[0]
    return off, hs, w, h, bpp, clrused

def read_24(p):
    off, hs, w, h, bpp, clrused = hdr(p)
    assert bpp == 24, (p, bpp)
    rowbytes = ((w * 3 + 3) // 4) * 4
    with open(p, "rb") as f:
        f.seek(off)
        raw = f.read(rowbytes * h)
    a = np.frombuffer(raw, dtype=np.uint8)[:rowbytes*h].reshape(h, rowbytes)[:, :w*3].reshape(h, w, 3)
    return a, w, h, rowbytes

def read_pal(p):
    off, hs, w, h, bpp, clrused = hdr(p)
    ps = 14 + hs
    n = (off - ps) // 4
    with open(p, "rb") as f:
        f.seek(ps)
        raw = f.read(n*4)
    arr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 4)
    return arr[:, [2, 1, 0]].astype(np.int16)   # -> RGB

L = []
vpal = read_pal(os.path.join(VAN, "terrain.bmp"))
L.append(f"vanilla palette entries={len(vpal)}")

for fn in ["terrain.bmp", "terrain_01.bmp"]:
    p = os.path.join(GAMMA, fn)
    if not os.path.exists(p):
        L.append(f"[MISSING] {fn}"); continue
    a, w, h, rb = read_24(p)
    L.append(f"\n########## {fn} 24bit {w}x{h} rowbytes={rb} bottom-up=True ##########")
    rgb = a.reshape(-1, 3).astype(np.int32)
    key = (rgb[:, 0] << 16) | (rgb[:, 1] << 8) | rgb[:, 2]
    uk, idx, cnt = np.unique(key, return_index=True, return_counts=True)
    order = np.argsort(-cnt)
    L.append(f"unique colors = {len(uk)}")
    # build lookup table of vanilla palette
    lut = {}
    for i in range(len(vpal)):
        c = (int(vpal[i][0]) << 16) | (int(vpal[i][1]) << 8) | int(vpal[i][2])
        lut.setdefault(c, []).append(i)
    for k in order:
        kk = int(uk[k]); r = (kk >> 16) & 255; g = (kk >> 8) & 255; b = kk & 255
        c = int(cnt[k])
        ex = lut.get(kk)
        if ex:
            tagtxt = "EXACT idx=" + ",".join(str(e) for e in ex)
        else:
            d = np.abs(vpal - np.array([r, g, b], dtype=np.int16)).sum(axis=1)
            j = int(np.argmin(d))
            tagtxt = f"NOEXACT nearest idx={j} RGB={tuple(int(x) for x in vpal[j])} L1={int(d[j])}"
        L.append(f"  RGB=({r:3d},{g:3d},{b:3d}) px={c:9d}  {tagtxt}")
        if k >= 80 and c < 200:
            L.append(f"  ... (stopping; remaining are tiny)")
            break

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("ok")

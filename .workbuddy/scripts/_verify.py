# -*- coding: utf-8 -*-
import struct, os, collections
import numpy as np

GAMMA = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
OUT   = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\scripts\_verify.txt"

def hdr(p):
    with open(p, "rb") as f:
        b = f.read(64)
    (off,) = struct.unpack_from("<I", b, 10)
    (hs,) = struct.unpack_from("<I", b, 14)
    w, h = struct.unpack_from("<ii", b, 18)
    planes, bpp = struct.unpack_from("<HH", b, 26)
    return off, hs, w, h, bpp

def read8(p):
    off, hs, w, h, bpp = hdr(p)
    assert bpp == 8, (p, bpp)
    with open(p, "rb") as f:
        f.seek(off)
        d = np.frombuffer(f.read(w*h), dtype=np.uint8).reshape(h, w)
    return d[::-1]   # top-down

def read24(p):
    off, hs, w, h, bpp = hdr(p)
    assert bpp == 24, (p, bpp)
    rb = ((w*3+3)//4)*4
    with open(p, "rb") as f:
        f.seek(off)
        raw = f.read(rb*h)
    a = np.frombuffer(raw, dtype=np.uint8).reshape(h, rb)[:, :w*3].reshape(h, w, 3)
    return a[::-1]   # top-down, BGR order

L = []
H = read8(os.path.join(GAMMA, "heightmap.bmp"))
C = read8(os.path.join(GAMMA, "cities.bmp"))
T = read24(os.path.join(GAMMA, "terrain.bmp"))
L.append(f"heightmap {H.shape} min={H.min()} max={H.max()}")
L.append(f"cities    {C.shape} values={sorted(set(C.ravel().tolist()))[:10]}")

ocean = H < 96
L.append(f"ocean(h<96) px = {int(ocean.sum())}  frac={ocean.mean():.4f}")
L.append(f"land (h>=96)  px = {int((~ocean).sum())}  frac={(~ocean).mean():.4f}")
L.append("")

# un-swap R/B -> the "true" RGB the palette intended
Ttrue = T[:, :, ::-1]            # BGR -> RGB
key = (Ttrue[:, :, 0].astype(np.int32) << 16) | (Ttrue[:, :, 1].astype(np.int32) << 8) | Ttrue[:, :, 2].astype(np.int32)
uk, cnt = np.unique(key, return_counts=True)
order = np.argsort(-cnt)

L.append("=== per-color spatial stats (R/B UN-swapped) ===")
L.append(f"{'RGB':>18} {'px':>9} {'meanH':>7} {'h<96%':>7} {'h>=160%':>8} {'cityPx':>8} {'city%':>7}")
for k in order:
    kk = int(uk[k]); r=(kk>>16)&255; g=(kk>>8)&255; b=kk&255
    m = key == kk
    n = int(m.sum())
    mh = float(H[m].mean())
    fo = float((H[m] < 96).mean())
    fh = float((H[m] >= 160).mean())
    cp = int((C[m] == 15).sum())
    L.append(f"  ({r:3d},{g:3d},{b:3d}) {n:9d} {mh:7.1f} {fo*100:6.2f}% {fh*100:7.2f}% {cp:8d} {cp/max(n,1)*100:6.1f}%")

# raw (no unswap) too, for contrast
key2 = (T[:,:,2].astype(np.int32)<<16) | (T[:,:,1].astype(np.int32)<<8) | T[:,:,0].astype(np.int32)
uk2, cnt2 = np.unique(key2, return_counts=True)
o2 = np.argsort(-cnt2)
L.append("")
L.append("=== per-color spatial stats (RAW, no unswap) top20 ===")
for k in o2[:20]:
    kk=int(uk2[k]); r=(kk>>16)&255; g=(kk>>8)&255; b=kk&255
    m = key2==kk; n=int(m.sum())
    L.append(f"  ({r:3d},{g:3d},{b:3d}) {n:9d} meanH={float(H[m].mean()):6.1f} h<96={float((H[m]<96).mean())*100:6.2f}%")

# terrain_02 index plane cross reference with cities.bmp
T2 = read8(os.path.join(GAMMA, "terrain_02.bmp"))
c2 = collections.Counter(T2.ravel().tolist())
L.append("")
L.append("=== terrain_02 index plane ===")
for i in sorted(c2):
    m = T2 == i
    L.append(f"  idx {i:3d}: px={c2[i]:9d} meanH={float(H[m].mean()):6.1f} h<96={float((H[m]<96).mean())*100:6.2f}% cityPx={int((C[m]==15).sum())}")

# overwrite test
L.append("")
t = os.path.join(GAMMA, "_ow_test.bin")
ok = []
try:
    with open(t, "wb") as f: f.write(b"AAA")
    ok.append("create-new: OK")
except Exception as e:
    ok.append(f"create-new: FAIL {e}")
try:
    with open(t, "wb") as f: f.write(b"BBB")
    ok.append("overwrite-existing: OK")
except Exception as e:
    ok.append(f"overwrite-existing: FAIL {e.__class__.__name__} {e}")
L.append("=== write test in gamma map dir ===")
L.extend("  " + x for x in ok)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("ok")

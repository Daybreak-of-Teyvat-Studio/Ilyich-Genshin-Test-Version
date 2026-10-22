# -*- coding: utf-8 -*-
"""Recompute buildings.txt col1 for state-level rows (col7==0) by map coordinates."""
import collections
import io
import os
import re
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
MOD = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
BP = os.path.join(MOD, "map", "buildings.txt")
DEF = os.path.join(MOD, "map", "definition.csv")
APPLY = "--apply" in sys.argv

p2s, kind, rgb = {}, {}, {}
for fn in os.listdir(os.path.join(MOD, "history", "states")):
    if fn.endswith(".txt"):
        t = io.open(os.path.join(MOD, "history", "states", fn), encoding="utf-8-sig").read()
        sid = int(fn.split("-")[0])
        for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", t).group(1).split():
            p2s[int(x)] = sid
for line in io.open(DEF, encoding="utf-8-sig", errors="replace"):
    a = line.split(";")
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
        rgb[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])

Image.MAX_IMAGE_PIXELS = None
arr = np.asarray(Image.open(os.path.join(MOD, "map", "provinces.bmp")).convert("RGB")).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
u, inv = np.unique(key, return_inverse=True)
pl = np.zeros(len(u), np.int32)
for i, k in enumerate(u):
    k = int(k)
    pl[i] = rgb.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = pl[inv].reshape(H, W)

raw = open(BP, "rb").read()
bom = raw[:3] == b"\xef\xbb\xbf"
text = raw.decode("utf-8-sig")
nl = "\r\n" if "\r\n" in text else "\n"
lines = text.split(nl)


def province_at(xf, zf):
    y, x = int(round(H - zf)), int(round(xf))
    if 0 <= y < H and 0 <= x < W and prov[y, x]:
        return int(prov[y, x])
    return None


changes = collections.Counter()
examples = []
for i, l in enumerate(lines):
    f = l.split(";")
    if len(f) != 7 or not f[0].isdigit() or not f[6].isdigit():
        continue
    if int(f[6]) != 0 or int(f[0]) not in (419, 421, 429):
        continue
    try:
        xf, zf = float(f[2]), float(f[4])
    except ValueError:
        continue
    p = province_at(xf, zf)
    if not p:
        continue
    st = p2s.get(p)
    if st is None:
        continue
    if st != int(f[0]):
        changes[(int(f[0]), st)] += 1
        if len(examples) < 12:
            examples.append((int(f[0]), st, f[1], p))
        f[0] = str(st)
        lines[i] = ";".join(f)

print("rows changed:", sum(changes.values()))
for (a, b), n in sorted(changes.items(), key=lambda kv: -kv[1])[:15]:
    print(f"   {a} -> {b}: {n}")
for e in examples:
    print("   ex", e)
if APPLY and changes:
    open(BP, "wb").write((b"\xef\xbb\xbf" if bom else b"") + nl.join(lines).encode())
    print("written")
elif not APPLY:
    print("[DRY]")

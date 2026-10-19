# -*- coding: utf-8 -*-
"""Recompute buildings.txt col1 for rows declared in 419/421/429 (naval snap rule)."""
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
ST = os.path.join(MOD, "history", "states")
for fn in os.listdir(ST):
    if fn.endswith(".txt"):
        t = io.open(os.path.join(ST, fn), encoding="utf-8-sig").read()
        sid = int(fn.split("-")[0])
        for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", t).group(1).split():
            p2s[int(x)] = sid
for line in io.open(DEF, encoding="utf-8-sig", errors="replace"):
    a = line.split(";")
    if len(a) > 6 and a[0].strip().isdigit():
        pid = int(a[0])
        kind[pid] = a[4]
        rgb[(int(a[1]), int(a[2]), int(a[3]))] = pid

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
land = np.isin(prov, [q for q, k2 in kind.items() if k2 == "land"])

NAVAL = {"naval_base_spawn", "naval_headquarters", "naval_supply_hub", "coastal_bunker", "floating_harbor"}
raw = open(BP, "rb").read()
bom = raw[:3] == b"\xef\xbb\xbf"
text = raw.decode("utf-8-sig")
nl = "\r\n" if "\r\n" in text else "\n"
lines = text.split(nl)
changes = []
for i, l in enumerate(lines):
    f = l.split(";")
    if len(f) != 7 or not f[0].isdigit() or not f[6].isdigit():
        continue
    decl, p7 = int(f[0]), int(f[6])
    if decl not in (419, 421, 429):
        continue
    target = None
    if p7 in p2s and kind.get(p7) == "land":
        target = p2s[p7]
    elif p7 and kind.get(p7) != "land" and f[1] in NAVAL:
        y, x = int(round(H - float(f[4]))), int(round(float(f[2])))
        lp = None
        if 0 <= y < H and 0 <= x < W and land[y, x]:
            lp = int(prov[y, x])
        else:
            for r in range(1, 16):
                y0, y1 = max(0, y - r), min(H, y + r + 1)
                x0, x1 = max(0, x - r), min(W, x + r + 1)
                sl = land[y0:y1, x0:x1]
                if sl.any():
                    vals = prov[y0:y1, x0:x1][sl]
                    lp = int(collections.Counter(vals.tolist()).most_common(1)[0][0])
                    break
        if lp is not None:
            target = p2s.get(lp)
    if target is not None and target != decl:
        f[0] = str(target)
        lines[i] = ";".join(f)
        changes.append((decl, target, f[1], p7))

print("rows to change:", len(changes))
for c in changes:
    print("  ", c)
if APPLY and changes:
    open(BP, "wb").write((b"\xef\xbb\xbf" if bom else b"") + nl.join(lines).encode())
    print("written")
elif not APPLY:
    print("[DRY]")

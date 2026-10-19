# -*- coding: utf-8 -*-
"""Province adjacency from provinces.bmp + definition.csv."""
import io, os, sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
MOD = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
MAP = os.path.join(MOD, "map")

prov_type = {}
colors = {}
with io.open(os.path.join(MAP, "definition.csv"), encoding="utf-8-sig") as fh:
    for line in fh:
        parts = line.strip().split(";")
        if len(parts) < 6 or not parts[0].isdigit():
            continue
        pid = int(parts[0])
        colors[(int(parts[1]), int(parts[2]), int(parts[3]))] = pid
        prov_type[pid] = parts[4]

img = Image.open(os.path.join(MAP, "provinces.bmp")).convert("RGB")
arr = np.asarray(img)
print("bmp", arr.shape)

flat = arr.reshape(-1, 3)
ids = np.zeros(flat.shape[0], dtype=np.int32)
for rgb, pid in colors.items():
    mask = (flat[:, 0] == rgb[0]) & (flat[:, 1] == rgb[1]) & (flat[:, 2] == rgb[2])
    if mask.any():
        ids[mask] = pid
ids = ids.reshape(arr.shape[:2])
print("unique provinces in bmp:", len(np.unique(ids)))

# state map
p2s, sowner = {}, {}
ST = os.path.join(MOD, "history", "states")
for fn in os.listdir(ST):
    if not fn.endswith(".txt"):
        continue
    t = io.open(os.path.join(ST, fn), encoding="utf-8-sig").read()
    sid = int(__import__("re").search(r"(?m)^\s*id\s*=\s*(\d+)", t).group(1))
    m = __import__("re").search(r"(?m)^\s*provinces\s*=\s*\{([^}]*)\}", t)
    for x in (m.group(1).split() if m else []):
        p2s[int(x)] = sid
    om = __import__("re").search(r"(?m)^\s*owner\s*=\s*(\w+)", t)
    sowner[sid] = om.group(1) if om else None


def neighbors(pid):
    ys, xs = np.where(ids == pid)
    if len(ys) == 0:
        return []
    found = set()
    h, w = ids.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            y2 = np.clip(ys + dy, 0, h - 1)
            x2 = np.clip(xs + dx, 0, w - 1)
            found.update(np.unique(ids[y2, x2]).tolist())
    found.discard(pid)
    found.discard(0)
    return sorted(found)


for p in (1156, 1532, 2464, 292, 1395, 3433, 3435, 3441, 3456, 3481, 3485):
    nb = neighbors(p)
    land = [q for q in nb if prov_type.get(q) == "land"]
    info = ", ".join(f"p{q}(s{p2s.get(q)}, {prov_type.get(q)})" for q in land)
    print(f"p{p} ({prov_type.get(p)}): land neighbors -> {info}")

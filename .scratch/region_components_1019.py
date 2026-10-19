# -*- coding: utf-8 -*-
"""Connected components of land provinces inside region 1 (from provinces.bmp)."""
import io, os, sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
MOD = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
MAP = os.path.join(MOD, "map")

colors, ptype = {}, {}
with io.open(os.path.join(MAP, "definition.csv"), encoding="utf-8-sig") as fh:
    for line in fh:
        p = line.strip().split(";")
        if len(p) < 6 or not p[0].isdigit():
            continue
        colors[(int(p[1]), int(p[2]), int(p[3]))] = int(p[0])
        ptype[int(p[0])] = p[4]

arr = np.asarray(Image.open(os.path.join(MAP, "provinces.bmp")).convert("RGB"))
flat = arr.reshape(-1, 3)
ids = np.zeros(flat.shape[0], dtype=np.int32)
for rgb, pid in colors.items():
    ids[(flat[:, 0] == rgb[0]) & (flat[:, 1] == rgb[1]) & (flat[:, 2] == rgb[2])] = pid
ids = ids.reshape(arr.shape[:2])

# region 1 provinces
r1 = set()
with io.open(os.path.join(MOD, "map", "strategicregions", "DOT_Strategicregions_01.txt"), encoding="utf-8-sig") as fh:
    t = fh.read()
pr = t.split("provinces={")[1].split("}")[0]
r1 = {int(x) for x in pr.split() if x.isdigit()}

pairs = set()
h1, h2 = ids[:, :-1], ids[:, 1:]
m = (h1 != h2) & (h1 > 0) & (h2 > 0)
pairs.update(map(tuple, np.unique(np.stack([h1[m], h2[m]], 1), axis=0)))
v1, v2 = ids[:-1, :], ids[1:, :]
m = (v1 != v2) & (v1 > 0) & (v2 > 0)
pairs.update(map(tuple, np.unique(np.stack([v1[m], v2[m]], 1), axis=0)))
print("adjacency pairs:", len(pairs))

# only land-land edges
land_pairs = [(a, b) for a, b in pairs if ptype.get(a) == "land" and ptype.get(b) == "land"
              and a in r1 and b in r1]
print("land-land edges in R1:", len(land_pairs))

parent = {}


def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra


for a, b in land_pairs:
    union(a, b)

comp = {}
for p in r1:
    if ptype.get(p) == "land":
        comp.setdefault(find(p), []).append(p)

comps = sorted(comp.values(), key=len, reverse=True)
print("land components in R1:", len(comps), [len(c) for c in comps[:10]])
for c in comps[1:6]:
    print("  isolated:", sorted(c))

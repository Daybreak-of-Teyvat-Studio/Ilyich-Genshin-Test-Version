# -*- coding: utf-8 -*-
"""直接比较两份 24 位手绘稿：final5(base 114209) vs terrain_24bit_painting，并统计灰/紫城市。"""
import os, io, struct, collections
import numpy as np

MAP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
REPORT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_24bit_cmp.txt"
lines = []
P = lambda s='': lines.append(s)


def read24(p):
    with open(p, 'rb') as f:
        b = f.read(64)
    off = struct.unpack_from('<I', b, 10)[0]
    w, h = struct.unpack_from('<ii', b, 18)
    row = (w * 3 + 3) & ~3
    with open(p, 'rb') as f:
        f.seek(off)
        d = np.frombuffer(f.read(row * h), dtype=np.uint8).reshape(h, row)[:, :w * 3]
    d = d.reshape(h, w, 3)[:, :, ::-1]  # BGR -> RGB
    return d[::-1]


A = read24(os.path.join(MAP, "terrain_final5.bmp"))
B = read24(os.path.join(MAP, "terrain_24bit_painting.bmp"))
P(f"final5           {A.shape}")
P(f"24bit_painting   {B.shape}")
P(f"逐像素不同 = {int((A != B).any(axis=2).sum()):,} / {A.shape[0]*A.shape[1]:,}")

for nm, X in (("final5", A), ("24bit_painting", B)):
    flat = X.reshape(-1, 3)
    c = collections.Counter(map(tuple, flat[::7]))
    P("")
    P(f"[{nm}] 颜色直方图（1/7 抽样，折算全量约 x7）:")
    for col, n in c.most_common(14):
        P(f"    {col}  ~{n*7:,} px")

P("")
P("灰色城市 (128,128,128) 精确像素数:")
for nm, X in (("final5", A), ("24bit_painting", B)):
    m = (X[:, :, 0] == 128) & (X[:, :, 1] == 128) & (X[:, :, 2] == 128)
    P(f"    {nm:16s} {int(m.sum()):,} px")
P("紫色城市 (155,0,255) 精确像素数:")
for nm, X in (("final5", A), ("24bit_painting", B)):
    m = (X[:, :, 0] == 155) & (X[:, :, 1] == 0) & (X[:, :, 2] == 255)
    P(f"    {nm:16s} {int(m.sum()):,} px")

P("")
P("按最近邻到已知 11 色的归类（抽样 1/13）:")
KNOWN = {(255, 129, 66): "plains0", (89, 199, 85): "forest1", (255, 63, 0): "desert3",
         (27, 27, 27): "mtn6", (76, 96, 35): "marsh9", (124, 135, 125): "mtn11",
         (128, 128, 128): "urban13", (0, 255, 255): "lakes14", (0, 0, 255): "ocean15",
         (248, 255, 153): "hills17", (127, 191, 0): "jungle21", (0, 0, 0): "black?"}
keys = np.array(list(KNOWN.keys()), dtype=np.int32)
names = list(KNOWN.values())
for nm, X in (("final5", A), ("24bit_painting", B)):
    s = X[::13, ::13].reshape(-1, 3).astype(np.int32)
    d = ((s[:, None, :] - keys[None, :, :]) ** 2).sum(axis=2)
    lab = d.argmin(axis=1)
    dist = d.min(axis=1)
    cnt = collections.Counter(lab.tolist())
    tot = len(lab)
    P(f"    [{nm}]  精确命中率 = {float((dist == 0).mean())*100:.3f}%")
    for k, n in cnt.most_common():
        P(f"        {names[k]:9s} {n*169:>10,} px  ({n/tot*100:5.2f}%)")

with io.open(REPORT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("ok")

# -*- coding: utf-8 -*-
"""把当前 terrain.bmp 逐索引拆成掩膜，和 cities.bmp 的城市掩膜对位，判断'灰色'到底是什么。"""
import os, io, struct, collections
import numpy as np
from PIL import Image

MAP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
PREV = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\preview"
REPORT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_gray.txt"
os.makedirs(PREV, exist_ok=True)
lines = []
P = lambda s='': lines.append(s)


def read_idx(p):
    with open(p, 'rb') as f:
        b = f.read(64)
    off = struct.unpack_from('<I', b, 10)[0]
    w, h = struct.unpack_from('<ii', b, 18)
    with open(p, 'rb') as f:
        f.seek(off)
        d = np.frombuffer(f.read(w * h), dtype=np.uint8).reshape(h, w)
    return d[::-1]


cur = read_idx(os.path.join(MAP, "terrain.bmp"))
cit = read_idx(os.path.join(MAP, "cities.bmp"))
P(f"terrain.bmp {cur.shape}   cities.bmp {cit.shape}")
P(f"cities.bmp 用到的索引：{collections.Counter(cit.ravel().tolist()).most_common()}")
city_mask = cit == 15
P(f"cities.bmp 索引15（城市掩膜）= {int(city_mask.sum()):,} px")

g11 = cur == 11
g13 = cur == 13
P("")
P(f"terrain.bmp idx11（灰 124,135,125） = {int(g11.sum()):,} px")
P(f"   其中落在 cities.bmp 城市掩膜内 = {int((g11 & city_mask).sum()):,} px")
P(f"   城市掩膜被 idx11 覆盖的部分 = {int((g11 & city_mask).sum()):,} / {int(city_mask.sum()):,}")
P(f"terrain.bmp idx13（紫 155,0,255） = {int(g13.sum()):,} px")
P(f"   其中落在 cities.bmp 城市掩膜内 = {int((g13 & city_mask).sum()):,} px")

# 连通块统计，看 idx11 是"山脉带"还是"城市团"
from scipy import ndimage as ndi
for nm, m in (("idx11 灰", g11), ("cities 掩膜", city_mask), ("idx13 紫", g13)):
    lab, n = ndi.label(m, np.ones((3, 3)))
    sz = np.bincount(lab.ravel())[1:]
    if len(sz):
        P(f"   [{nm}] 连通块 {n} 个，最大 {sz.max():,}，中位 {int(np.median(sz))}，前5大 = {[int(x) for x in sorted(sz)[-5:][::-1]]}")

# 出图：灰(idx11)掩膜 / 城市掩膜 / 灰∩非城市
h, w = cur.shape
def rgba(mask, col):
    o = np.zeros((h, w, 3), dtype=np.uint8)
    o[mask] = col
    return o
a = rgba(g11, (200, 200, 200))
b = rgba(city_mask, (255, 60, 60))
c = rgba(g11 & ~city_mask, (120, 160, 255))
gap = np.full((h, 6, 3), 255, dtype=np.uint8)
img = Image.fromarray(np.concatenate([a, gap, b, gap, c], axis=1))
img = img.resize((img.width // 6, img.height // 6), Image.NEAREST)
out = os.path.join(PREV, "gray_breakdown.png")
img.save(out)
P("")
P(f"三联图（左=idx11 灰 / 中=cities.bmp 城市掩膜 / 右=灰中不属于城市的部分）-> {out}")

with io.open(REPORT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("ok")

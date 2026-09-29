# -*- coding: utf-8 -*-
"""对比 final5_8bit 与当前装机 terrain.bmp 的像素差异，并出对照预览。"""
import os, io, struct, collections
import numpy as np
from PIL import Image

MAP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
PREV = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\preview"
REPORT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_final5_diff.txt"

lines = []
P = lambda s='': lines.append(s)


def read8(p):
    with open(p, 'rb') as f:
        b = f.read(64)
    off = struct.unpack_from('<I', b, 10)[0]
    w, h = struct.unpack_from('<ii', b, 18)
    with open(p, 'rb') as f:
        f.seek(off)
        d = np.frombuffer(f.read(w * h), dtype=np.uint8).reshape(h, w)
    return d[::-1]  # 行自下而上 -> 正立


a = read8(os.path.join(MAP, "terrain_final5_8bit.bmp"))
b = read8(os.path.join(MAP, "terrain.bmp"))
P(f"final5_8bit shape={a.shape}   terrain.bmp shape={b.shape}")
P(f"差异像素 = {int((a != b).sum()):,}  /  {a.size:,}  ({(a != b).mean()*100:.3f}%)")
P("")
P("差异索引对（final5 索引 -> terrain.bmp 索引）前 15 名：")
IDX2NAME = {0: "plains", 1: "forest", 2: "hills", 3: "desert", 6: "mountain", 9: "marsh",
            11: "mountain", 13: "urban", 14: "lakes", 15: "ocean", 17: "hills",
            21: "jungle", 27: "mountain"}
m = a != b
pairs = collections.Counter(zip(a[m].tolist(), b[m].tolist()))
for (x, y), c in pairs.most_common(15):
    P(f"   idx{x:3d}({IDX2NAME.get(x,'?'):8s}) -> idx{y:3d}({IDX2NAME.get(y,'?'):8s})  {c:>9,} px")

P("")
P("仅出现在 final5_8bit 的索引：" + str(sorted(set(np.unique(a).tolist()) - set(np.unique(b).tolist()))))
P("仅出现在 terrain.bmp 的索引：" + str(sorted(set(np.unique(b).tolist()) - set(np.unique(a).tolist()))))

# ---- 对照预览：主陆区裁切，两个版本并排 ----
# 主陆包围盒（按 summary 记录的龙脊/主陆位置取一块）
y0, y1, x0, x1 = 400, 1100, 1500, 2700
PAL_FIX = {}
IDX_COLOR = {0: (255, 129, 66), 1: (89, 199, 85), 3: (255, 63, 0), 6: (27, 27, 27),
             9: (76, 96, 35), 11: (124, 135, 125), 13: (128, 128, 128),
             14: (0, 255, 255), 15: (0, 0, 255), 17: (248, 255, 153), 21: (127, 191, 0),
             27: (0, 0, 0)}


def render(arr):
    h, w = arr.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    for k, c in IDX_COLOR.items():
        out[arr == k] = c
    return out


ca, cb = a[y0:y1, x0:x1], b[y0:y1, x0:x1]
ra, rb = render(ca), render(cb)
gap = np.full((ra.shape[0], 8, 3), 255, dtype=np.uint8)
side = np.concatenate([ra, gap, rb], axis=1)
img = Image.fromarray(side)
img = img.resize((img.width // 2, img.height // 2), Image.NEAREST)
p1 = os.path.join(PREV, "cmp_final5_vs_current.png")
img.save(p1)
P("")
P(f"对照预览（左=final5_8bit，右=当前 terrain.bmp，裁切 y{y0}:{y1} x{x0}:{x1}）-> {p1}")

# ---- 城市区域放大，确认灰/紫 ----
ys, xs = np.where(a == 13)
if len(ys):
    cy, cx = int(ys.mean()), int(xs.mean())
    P(f"城市像素质心 y={cy} x={cx}，共 {len(ys)} px")
    y2, y3 = max(0, cy - 150), cy + 150
    x2, x3 = max(0, cx - 150), cx + 150
    za = render(a[y2:y3, x2:x3])
    zb = render(b[y2:y3, x2:x3])
    g = np.full((za.shape[0], 8, 3), 255, dtype=np.uint8)
    z = Image.fromarray(np.concatenate([za, g, zb], axis=1))
    z = z.resize((z.width * 2, z.height * 2), Image.NEAREST)
    p2 = os.path.join(PREV, "cmp_final5_city_zoom.png")
    z.save(p2)
    P(f"城市区放大（左=final5_8bit 紫，右=当前 灰）-> {p2}")

with io.open(REPORT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("ok")

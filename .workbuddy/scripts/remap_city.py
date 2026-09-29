# -*- coding: utf-8 -*-
"""按用户指令重编 terrain.bmp 的地形索引：
   绿色（森林1 / 沼泽9 / 丛林21）→ 平原0
   紫色（13）→ 平原0
   灰色（11）中与 cities.bmp 城市掩膜重合的部分 → 城市13
   其余索引一字不动。调色板仅改第 13 号色槽的城市显示色。
"""
import os, io, struct, shutil, collections, hashlib
import numpy as np
from PIL import Image

MAP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
WB = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy"
PREV = os.path.join(WB, "preview")
BK = os.path.join(WB, "backup_20260924_1538")
REPORT = os.path.join(WB, "report_city_remap.txt")
os.makedirs(PREV, exist_ok=True)
os.makedirs(BK, exist_ok=True)

lines = []
P = lambda s='': lines.append(s)

SRC = os.path.join(MAP, "terrain.bmp")
CITY = os.path.join(MAP, "cities.bmp")
OUTMAP = os.path.join(MAP, "terrain_04.bmp")
OUTWB = os.path.join(WB, "terrain_04.bmp")


def hdr(p):
    with open(p, 'rb') as f:
        b = f.read(64)
    return dict(off=struct.unpack_from('<I', b, 10)[0],
                dib=struct.unpack_from('<I', b, 14)[0],
                w=struct.unpack_from('<ii', b, 18)[0], h=struct.unpack_from('<ii', b, 18)[1],
                bpp=struct.unpack_from('<HH', b, 26)[1],
                comp=struct.unpack_from('<I', b, 30)[0],
                clrused=struct.unpack_from('<I', b, 46)[0],
                size=os.path.getsize(p))


def read_index(p):
    H = hdr(p)
    n = H['clrused'] or (H['off'] - 14 - H['dib']) // 4
    with open(p, 'rb') as f:
        raw = f.read()
    pal = [tuple(raw[14 + H['dib'] + i * 4: 14 + H['dib'] + i * 4 + 3][::-1]) for i in range(n)]
    need = H['w'] * abs(H['h'])
    trail = len(raw) - H['off'] - need
    if trail:
        P(f"  [{os.path.basename(p)}] 像素体后还有 {trail} 个多余字节，"
          f"文件长 {len(raw):,}，off+W*H = {H['off'] + need:,}；本次按 off+W*H 截断写出")
    body = np.frombuffer(raw[H['off']:H['off'] + need], dtype=np.uint8).reshape(abs(H['h']), H['w'])
    return raw, H, pal, body[::-1]


P("=== 0. 备份 ===")
for src, nm in ((SRC, "terrain.bmp"), (CITY, "cities.bmp")):
    dst = os.path.join(BK, nm)
    if os.path.exists(dst):
        P(f"  {dst}  已存在，跳过")
        continue
    try:
        shutil.copy2(src, dst)
        P(f"  {dst}")
    except PermissionError:
        P(f"  {dst}  写入被拒（沙箱不允许覆盖），跳过")

raw, H, pal, idx = read_index(SRC)
_, Hc, _, cidx = read_index(CITY)
P("")
P("=== 1. 输入 ===")
P(f"  terrain.bmp {H['size']:,} B  {H['w']}x{H['h']} bpp={H['bpp']} off={H['off']} clrUsed={H['clrused']} 色槽={len(pal)}")
P(f"  cities.bmp  {Hc['size']:,} B  off={Hc['off']} clrUsed={Hc['clrused']}")

city_mask = cidx == 15
P(f"  城市掩膜（cities.bmp 索引 15）= {int(city_mask.sum()):,} px")

before = collections.Counter(idx.ravel().tolist())
P("")
P("=== 2. 改动前索引直方图 ===")
for k in sorted(before):
    P(f"   idx {k:3d}  {before[k]:>10,} px  色={pal[k] if k < len(pal) else 'N/A'}")

# ---- 变换 ----
g1 = idx == 1
g9 = idx == 9
g21 = idx == 21
g13 = idx == 13
g11 = idx == 11
hit = g11 & city_mask
keep11 = g11 & ~city_mask

P("")
P("=== 3. 变换明细 ===")
P(f"  森林 idx1  {int(g1.sum()):>9,} px -> 平原 0")
P(f"  沼泽 idx9  {int(g9.sum()):>9,} px -> 平原 0")
P(f"  丛林 idx21 {int(g21.sum()):>9,} px -> 平原 0")
P(f"  紫色 idx13 {int(g13.sum()):>9,} px -> 平原 0")
P(f"  灰色 idx11 ∩ 城市掩膜 {int(hit.sum()):>9,} px -> 城市 13")
P(f"  灰色 idx11 其余        {int(keep11.sum()):>9,} px -> 保持 11（山地）")
P(f"  城市掩膜未被灰覆盖       {int((city_mask & ~g11).sum()):>9,} px  只报不改")

out = idx.copy()
out[g1 | g9 | g21 | g13] = 0
out[hit] = 13

changed = out != idx
P(f"  实际改动像素合计 = {int(changed.sum()):,}")
P(f"  校验：期望 = {int((g1|g9|g21|g13).sum()) + int(hit.sum()):,}  "
  f"（g1+g9+g21+g13 互斥，hit ⊂ g11 且与它们不相交）")

# ---- 调色板：只改 13 号色槽 ----
pal_new = list(pal)
pal_new[13] = (128, 128, 128)
P("")
P("=== 4. 调色板 ===")
P(f"  idx13 城市显示色 {pal[13]} -> {pal_new[13]}")
P("  （其余色槽一字不动；游戏的 terrain 判定读索引、不读调色板色）")

# ---- 写盘：逐字节保留原头结构 ----
blob = bytearray(raw)
for i, (r, g, b) in enumerate(pal_new):
    base = 14 + H['dib'] + i * 4
    blob[base], blob[base + 1], blob[base + 2], blob[base + 3] = b, g, r, 0
body = out[::-1, :].tobytes()
blob = bytearray(bytes(blob[:H['off']]) + body)
struct.pack_into('<I', blob, 2, len(blob))
struct.pack_into('<I', blob, 34, len(body))

with open(OUTMAP, 'wb') as f:
    f.write(bytes(blob))
def put(path, data):
    """写文件；被沙箱拒写时退到带时间戳的同目录名，并回报实际路径。"""
    import time
    try:
        with open(path, 'wb') as fh:
            fh.write(data)
        return path
    except PermissionError:
        alt = path.replace(".bmp", f"_{int(time.time())}.bmp")
        with open(alt, 'wb') as fh:
            fh.write(data)
        P(f"  {path} 被拒写，改写到 {alt}")
        return alt


P("")
P("=== 5. 写出 ===")
OUTMAP = put(OUTMAP, bytes(blob))
P(f"  {OUTMAP}  {os.path.getsize(OUTMAP):,} B")
OUTWB = put(OUTWB, bytes(blob))
P(f"  {OUTWB}  {os.path.getsize(OUTWB):,} B")

# ---- 回读校验 ----
raw2, H2, pal2, idx2 = read_index(OUTMAP)
P(f"  回读 bpp={H2['bpp']} off={H2['off']} clrUsed={H2['clrused']}  尺寸={H2['w']}x{H2['h']}")
P(f"  回读索引与内存逐像素一致 = {bool((idx2 == out).all())}")
P(f"  回读调色板 idx13 = {pal2[13]}  期望 {pal_new[13]}  一致 = {pal2[13] == pal_new[13]}")
P(f"  调色板其余项未被改动 = {all(pal2[i] == pal[i] for i in range(len(pal)) if i != 13)}")
P(f"  头声明字节 {H2['size']:,} 与实物一致 = {H2['size'] == os.path.getsize(OUTMAP)}")

after = collections.Counter(out.ravel().tolist())
P("")
P("=== 6. 改动后索引直方图 ===")
IDX2NAME = {0: "plains", 1: "forest", 2: "hills", 3: "desert", 6: "mountain", 9: "marsh",
            11: "mountain", 13: "urban", 14: "lakes", 15: "ocean", 17: "hills", 21: "jungle"}
undef = [k for k in sorted(after) if k not in IDX2NAME]
for k in sorted(after):
    P(f"   idx {k:3d}  {after[k]:>10,} px  {IDX2NAME.get(k,'未定义'):9s} 色={pal_new[k] if k < len(pal_new) else 'N/A'}")
P(f"  未定义索引 = {undef if undef else '无'}")
P(f"  像素总数 = {sum(after.values()):,}（应为 8,388,608）")

# ---- 预览 ----
IDXC = dict(zip(range(len(pal_new)), pal_new))
IDXC[13] = (128, 128, 128)
IDXC[11] = (124, 135, 125)


def render(a):
    o = np.zeros((a.shape[0], a.shape[1], 3), dtype=np.uint8)
    for k in np.unique(a).tolist():
        o[a == k] = IDXC.get(k, (255, 0, 0))
    return o


img = Image.fromarray(render(out))
img.resize((1024, 512), Image.NEAREST).save(os.path.join(PREV, "terrain_04_preview.png"))
P("")
P("=== 7. 预览 ===")
P(f"  全图 -> {os.path.join(PREV, 'terrain_04_preview.png')}")

# 城市放大：取最大城市块
from scipy import ndimage as ndi
lab, n = ndi.label(hit, np.ones((3, 3)))
sz = np.bincount(lab.ravel())
big = int(np.argmax(sz[1:])) + 1
cy, cx = [int(v) for v in ndi.center_of_mass(lab == big)]
P(f"  最大城市块 {int(sz[big]):,} px，中心 y={cy} x={cx}")
y0, x0 = max(0, cy - 90), max(0, cx - 90)
z = Image.fromarray(render(out[y0:y0 + 180, x0:x0 + 180])).resize((540, 540), Image.NEAREST)
z.save(os.path.join(PREV, "terrain_04_city_zoom.png"))
P(f"  城市放大 -> {os.path.join(PREV, 'terrain_04_city_zoom.png')}")

# 改动标注图
ann = render(out)
ann[changed] = (255, 0, 0)
Image.fromarray(ann).resize((1024, 512), Image.NEAREST).save(os.path.join(PREV, "terrain_04_changed.png"))
P(f"  改动区标注（红）-> {os.path.join(PREV, 'terrain_04_changed.png')}")
P(f"  改动像素 {int(changed.sum()):,}，占全图 {changed.mean()*100:.2f}%，占陆地 "
  f"{changed.sum()/max(1,(out>0).sum()):.3f}")

with io.open(REPORT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("ok")

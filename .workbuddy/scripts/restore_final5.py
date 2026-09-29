# -*- coding: utf-8 -*-
"""final5 系列：比对 hoi4lint 与 map 副本、生成调色板校正版、渲染预览。（可重入）"""
import os, io, struct, hashlib, collections

SRC = r"C:\Users\XIANGZIYUAN\hoi4lint"
MAP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
PREV = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\preview"
REPORT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_final5_restore.txt"
os.makedirs(PREV, exist_ok=True)

lines = []
P = lambda s='': lines.append(s)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def hdr(p):
    with open(p, 'rb') as f:
        b = f.read(64)
    return dict(off=struct.unpack_from('<I', b, 10)[0],
                dib=struct.unpack_from('<I', b, 14)[0],
                w=struct.unpack_from('<ii', b, 18)[0],
                h=struct.unpack_from('<ii', b, 18)[1],
                bpp=struct.unpack_from('<HH', b, 26)[1],
                clrused=struct.unpack_from('<I', b, 46)[0],
                size=os.path.getsize(p))


P("=== 一、map 目录副本 vs hoi4lint 存档 逐字节比对 ===")
for nm in ("terrain_final5.bmp", "terrain_final5_8bit.bmp"):
    a = os.path.join(SRC, nm)
    b = os.path.join(MAP, nm)
    if not os.path.exists(b):
        P(f"  {nm}: map 副本缺失")
        continue
    ma, mb = md5(a), md5(b)
    H = hdr(b)
    P(f"  {nm}")
    P(f"    map  : {H['size']:,} 字节  bpp={H['bpp']}  偏移={H['off']}  色槽={H['clrused']}  md5={mb}")
    P(f"    存档 : md5={ma}   逐字节一致={ma == mb}")

P("")
P("=== 二、生成调色板校正版（像素零改动，仅第 13 号色槽 155,0,255 -> 128,128,128）===")
src8 = os.path.join(SRC, "terrain_final5_8bit.bmp")
H = hdr(src8)
pal_base = 14 + H['dib']
n_ent = H['clrused'] or (H['off'] - pal_base) // 4
with open(src8, 'rb') as f:
    raw = bytearray(f.read())
P(f"  色板基址 {pal_base}，项数 {n_ent}")
old = tuple(raw[pal_base + 13 * 4: pal_base + 13 * 4 + 3][::-1])
raw[pal_base + 13 * 4] = 128
raw[pal_base + 13 * 4 + 1] = 128
raw[pal_base + 13 * 4 + 2] = 128
raw[pal_base + 13 * 4 + 3] = 0
new = tuple(raw[pal_base + 13 * 4: pal_base + 13 * 4 + 3][::-1])
P(f"  idx13 调色板由 {old} 改为 {new}")

fixed_path = os.path.join(MAP, "terrain_final5_8bit_fixed.bmp")
try:
    with open(fixed_path, 'wb') as fh:
        fh.write(bytes(raw))
except PermissionError:
    P("  map 下同名文件已存在（沙箱禁止覆盖），改写到 .workbuddy")
    fixed_path = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\terrain_final5_8bit_fixed.bmp"
    with open(fixed_path, 'wb') as fh:
        fh.write(bytes(raw))
Hf = hdr(fixed_path)
P(f"  写出 {fixed_path}")
P(f"    {Hf['size']:,} 字节  bpp={Hf['bpp']}  偏移={Hf['off']}  色槽={Hf['clrused']}  md5={md5(fixed_path)}")
# 校验像素区完全未被改动
with open(fixed_path, 'rb') as fh:
    fh.seek(Hf['off'])
    fixed_px = fh.read()
with open(src8, 'rb') as fh:
    fh.seek(H['off'])
    ref_px = fh.read()
P(f"  像素区与原件逐字节一致 = {fixed_px == ref_px}")

P("")
P("=== 三、索引直方图（对照 00_terrain.txt 已定义编号）===")
IDX2NAME = {0: "plains", 1: "forest", 2: "hills", 3: "desert", 4: "forest", 5: "plains",
            6: "mountain", 7: "desert", 8: "desert", 9: "marsh", 10: "mountain",
            11: "mountain", 12: "desert", 13: "urban", 14: "lakes", 15: "ocean",
            16: "mountain", 17: "hills", 18: "mountain", 19: "plains", 20: "mountain",
            21: "jungle", 22: "jungle", 27: "mountain", 31: "mountain"}


def scan8(path, tag):
    H2 = hdr(path)
    with open(path, 'rb') as f:
        f.seek(14 + H2['dib'])
        palraw = f.read(n_ent * 4)
    pal = [tuple(palraw[i * 4:i * 4 + 3][::-1]) for i in range(n_ent)]
    with open(path, 'rb') as f:
        f.seek(H2['off'])
        data = f.read(H2['w'] * abs(H2['h']))
    hist = collections.Counter(data)
    undef = [k for k in sorted(hist) if k not in IDX2NAME]
    P(f"  [{tag}] 用到 {len(hist)} 个索引；未定义编号 = {undef if undef else '无'}")
    for k in sorted(hist):
        P(f"      idx {k:3d}  {hist[k]:>10,} px   {IDX2NAME.get(k, '未定义'):9s} 调色板色={pal[k] if k < len(pal) else 'N/A'}")


scan8(os.path.join(MAP, "terrain_final5_8bit.bmp"), "map/final5_8bit")
scan8(fixed_path, "final5_8bit_fixed")

P("")
P("=== 四、预览渲染 ===")
from PIL import Image
for src, out in ((os.path.join(MAP, "terrain_final5_8bit.bmp"), "final5_8bit_preview.png"),
                 (fixed_path, "final5_8bit_fixed_preview.png")):
    try:
        im = Image.open(src)
        P(f"  PIL 载入 {os.path.basename(src)} mode={im.mode} size={im.size}")
        rgb = im.convert("RGBA")
        # 城市层单独放大预览
        rgb.resize((1024, 512), Image.NEAREST).save(os.path.join(PREV, out))
        P(f"    -> {os.path.join(PREV, out)}")
    except Exception as e:
        P(f"  预览失败 {src}: {e}")

with io.open(REPORT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("ok")

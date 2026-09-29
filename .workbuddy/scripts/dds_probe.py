# -*- coding: utf-8 -*-
"""解析若干 DDS 头，确认本项目/HOI4 使用的像素格式。"""
import os
import struct

FILES = [
    r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry\PRC_infantry_diffuse.dds",
    r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry\PRC_infantry_normal.dds",
    r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\gfx\models\units\DOT_Keqing\clothesCHI.dds",
    r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\gfx\models\units\DOT_Keqing\clothesCHI_normal.dds",
    r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\gfx\models\units\DOT_Keqing\nospe_CHI.dds",
    r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\gfx\models\units\ENG_infantry_diffuse.dds",
    r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\gfx\models\units\ENG_infantry_normal.dds",
]

FOURCC = {b"DXT1": "DXT1/BC1", b"DXT2": "DXT2", b"DXT3": "DXT3/BC2",
          b"DXT4": "DXT4", b"DXT5": "DXT5/BC3", b"ATI1": "BC4", b"ATI2": "BC5",
          b"BC4U": "BC4U", b"BC5U": "BC5U", b"DX10": "DX10(ext)"}
DDPF = [("ALPHAPIXELS", 0x1), ("ALPHA", 0x2), ("FOURCC", 0x4), ("RGB", 0x40),
        ("YUV", 0x200), ("LUMINANCE", 0x20000)]
DDSD = [("CAPS", 0x1), ("HEIGHT", 0x2), ("WIDTH", 0x4), ("PITCH", 0x8),
        ("PIXELFORMAT", 0x1000), ("MIPMAPCOUNT", 0x20000), ("LINEARSIZE", 0x80000),
        ("DEPTH", 0x800000)]


def flags(v, table):
    return [n for n, b in table if v & b]


out = []
for f in FILES:
    name = os.path.basename(f)
    out.append("=" * 78)
    if not os.path.isfile(f):
        out.append(f"{name}: 缺失")
        continue
    raw = open(f, "rb").read(148)
    magic = raw[:4]
    (size, flg, h, w, pitch, depth, mip) = struct.unpack_from("<7I", raw, 4)
    pf = struct.unpack_from("<8I", raw, 76)
    pfsize, pfflg, fourcc, rgbbits, rmask, gmask, bmask, amask = pf
    caps = struct.unpack_from("<5I", raw, 108)
    out.append(f"{name}   {os.path.getsize(f):,} bytes  magic={magic!r}")
    out.append(f"    {w} x {h}  mip={mip}  pitch={pitch}  flags={flags(flg, DDSD)}")
    fc = struct.pack("<I", fourcc)
    out.append(f"    pf: size={pfsize} flags={flags(pfflg, DDPF)} fourcc={fc!r} {FOURCC.get(fc,'')}")
    out.append(f"        bits={rgbbits} R={rmask:#x} G={gmask:#x} B={bmask:#x} A={amask:#x}")
    out.append(f"    caps={caps}")

txt = "\n".join(out)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_dds.txt"),
     "w", encoding="utf-8").write(txt)
print(txt)

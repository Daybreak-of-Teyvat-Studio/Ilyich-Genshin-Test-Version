# -*- coding: utf-8 -*-
"""体检当前 terrain.bmp / terrain_03 / terrain_00 / terrain_01 的真实格式与色彩构成。"""
import os, io, struct, collections
import numpy as np

MAP = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map"
REPORT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_now.txt"
lines = []
P = lambda s='': lines.append(s)

IDX2NAME = {0: "plains", 1: "forest", 2: "hills", 3: "desert", 4: "forest", 5: "plains",
            6: "mountain", 7: "desert", 8: "desert", 9: "marsh", 10: "mountain",
            11: "mountain", 12: "desert", 13: "urban", 14: "lakes", 15: "ocean",
            16: "mountain", 17: "hills", 18: "mountain", 19: "plains", 20: "mountain",
            21: "jungle", 22: "jungle", 27: "mountain", 31: "mountain"}


def hdr(p):
    with open(p, 'rb') as f:
        b = f.read(64)
    return dict(sig=b[0:2], fsize=struct.unpack_from('<I', b, 2)[0],
                off=struct.unpack_from('<I', b, 10)[0],
                dib=struct.unpack_from('<I', b, 14)[0],
                w=struct.unpack_from('<ii', b, 18)[0], h=struct.unpack_from('<ii', b, 18)[1],
                bpp=struct.unpack_from('<HH', b, 26)[1],
                comp=struct.unpack_from('<I', b, 30)[0],
                clrused=struct.unpack_from('<I', b, 46)[0],
                size=os.path.getsize(p))


for nm in ("terrain.bmp", "terrain_03.bmp", "terrain_00.bmp", "terrain_01.bmp",
           "terrain_24bit_painting.bmp", "terrain_final5_8bit.bmp"):
    p = os.path.join(MAP, nm)
    if not os.path.exists(p):
        P(f"{nm}: 不存在")
        continue
    H = hdr(p)
    P("=" * 74)
    P(f"{nm}")
    P(f"  {H['size']:,} B   sig={H['sig']!r}  hdrSize={H['fsize']:,}  off={H['off']}  dib={H['dib']}")
    P(f"  {H['w']}x{H['h']}  bpp={H['bpp']}  comp={H['comp']}  clrUsed={H['clrused']}")
    P(f"  调色板字节={H['off']-14-H['dib']}  -> 项数={(H['off']-14-H['dib'])//4}")
    if H['bpp'] == 8:
        n = H['clrused'] or (H['off'] - 14 - H['dib']) // 4
        with open(p, 'rb') as f:
            f.seek(14 + H['dib'])
            pr = f.read(max(n, 256) * 4)
        pal = [tuple(pr[i * 4:i * 4 + 3][::-1]) for i in range(len(pr) // 4)]
        with open(p, 'rb') as f:
            f.seek(H['off'])
            d = f.read(H['w'] * abs(H['h']))
        P(f"  读到像素 {len(d):,}  (期望 {H['w']*abs(H['h']):,})")
        if len(d) == H['w'] * abs(H['h']):
            arr = np.frombuffer(d, dtype=np.uint8).reshape(abs(H['h']), H['w'])[::-1]
            hist = collections.Counter(arr.ravel().tolist())
            undef = [k for k in sorted(hist) if k not in IDX2NAME]
            P(f"  用到 {len(hist)} 个索引；未定义={undef if undef else '无'}")
            for k in sorted(hist):
                P(f"     idx {k:3d} {hist[k]:>10,} px  {IDX2NAME.get(k,'未定义'):9s} 色={pal[k] if k < len(pal) else 'N/A'}")
    elif H['bpp'] == 24:
        row = (H['w'] * 3 + 3) & ~3
        with open(p, 'rb') as f:
            f.seek(H['off'])
            d = f.read(row * abs(H['h']))
        a = np.frombuffer(d, dtype=np.uint8).reshape(abs(H['h']), row)[:, :H['w'] * 3]
        a = a.reshape(abs(H['h']), H['w'], 3)[:, :, ::-1][::-1]
        c = collections.Counter(map(tuple, a.reshape(-1, 3)[::11]))
        P(f"  24 位主要颜色（1/11 抽样，折算 x11）:")
        for col, k in c.most_common(16):
            P(f"     {col}  ~{k*11:,} px")

with io.open(REPORT, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("ok")

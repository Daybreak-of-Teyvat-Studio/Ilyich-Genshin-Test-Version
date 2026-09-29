# -*- coding: utf-8 -*-
"""buildings.txt 的坐标 vs 原版地图 Vanilla provinces.bmp。"""
import struct, os, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
VAN = r'C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\map'
REP = os.path.join(ROOT, '.workbuddy', 'report_vanilla_cmp.txt')

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

def load(raw):
    o = struct.unpack_from('<I', raw, 10)[0]
    W, H = struct.unpack_from('<ii', raw, 18)
    bpp = struct.unpack_from('<H', raw, 28)[0]
    if bpp != 24:
        return None, W, H, bpp
    rb = W * 3
    a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:rb * H].reshape(H, W, 3)
    v = (a[:, :, 2].astype(np.int32) << 16) | (a[:, :, 1].astype(np.int32) << 8) | a[:, :, 0].astype(np.int32)
    return v, W, H, bpp

P(f'原版地图目录存在: {os.path.isdir(VAN)}')
for f in ('provinces.bmp', 'definition.csv', 'buildings.txt'):
    p = os.path.join(VAN, f)
    P(f'   {f:<20} {"存在 " + str(os.path.getsize(p)) if os.path.exists(p) else "不存在"}')

vanb = os.path.join(VAN, 'buildings.txt')
if os.path.exists(vanb):
    lines = open(vanb, encoding='utf-8', errors='replace').read().splitlines()
    P(f'\n=== 原版 buildings.txt 前 8 行（共 {len(lines):,} 行）===')
    for l in lines[:8]:
        P('   ' + l)
    van_pids, vW, vH, vbpp = load(open(os.path.join(VAN, 'provinces.bmp'), 'rb').read())
    vdmap = {}
    for ln in open(os.path.join(VAN, 'definition.csv'), encoding='utf-8', errors='replace'):
        f2 = ln.strip().split(';')
        if len(f2) >= 5:
            try:
                vdmap[(int(f2[1]) << 16) | (int(f2[2]) << 8) | int(f2[3])] = int(f2[0])
            except ValueError:
                pass
    P(f'\n原版 provinces.bmp {vW}x{vH} {vbpp}bpp  definition {len(vdmap):,}')

    # 检验 MOD 的 buildings.txt 坐标落在原版地图上是否匹配它声明的省号
    P('\n=== MOD buildings.txt 坐标 打在 原版 provinces.bmp 上 ===')
    for tag, fn in (('row=z', lambda z: int(z)), ('row=H-1-z', lambda z: vH - 1 - int(z))):
        tot = hit = 0
        for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
            f = ln.strip().split(';')
            if len(f) < 6:
                continue
            try:
                pid = int(f[0]); x = float(f[2]); z = float(f[4])
            except ValueError:
                continue
            tot += 1
            r = fn(z); c = int(x)
            if 0 <= c < vW and 0 <= r < vH and vdmap.get(int(van_pids[r, c])) == pid:
                hit += 1
        P(f'   {tag:<12} {hit:,}/{tot:,} = {100.0*hit/tot:.2f}%')

    # 检验原版 buildings.txt 坐标 打在 原版地图
    P('\n=== 原版 buildings.txt 坐标 打在 原版 provinces.bmp 上 ===')
    for tag, fn in (('row=z', lambda z: int(z)), ('row=H-1-z', lambda z: vH - 1 - int(z))):
        tot = hit = 0
        for ln in lines:
            f = ln.strip().split(';')
            if len(f) < 6:
                continue
            try:
                pid = int(f[0]); x = float(f[2]); z = float(f[4])
            except ValueError:
                continue
            tot += 1
            r = fn(z); c = int(x)
            if 0 <= c < vW and 0 <= r < vH and vdmap.get(int(van_pids[r, c])) == pid:
                hit += 1
        P(f'   {tag:<12} {hit:,}/{tot:,} = {100.0*hit/tot:.2f}%')

# MOD buildings vs MOD 地图，但用原版 definition 的省号解释
P('\n=== MOD buildings.txt 坐标 打在 MOD provinces.bmp 上，两种 row 映射，放宽到「任意省」 ===')
mod_pids, mW, mH, mbpp = load(open(os.path.join(MAP, 'provinces.bmp'), 'rb').read())
for tag, fn in (('row=z', lambda z: int(z)), ('row=H-1-z', lambda z: mH - 1 - int(z))):
    inside = 0; tot = 0
    for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
        f = ln.strip().split(';')
        if len(f) < 6:
            continue
        try:
            x = float(f[2]); z = float(f[4])
        except ValueError:
            continue
        tot += 1
        r = fn(z); c = int(x)
        if 0 <= c < mW and 0 <= r < mH and mod_pids[r, c] != 0:
            inside += 1
    P(f'   {tag:<12} 落在「某个有效省像素」上 {inside:,}/{tot:,} = {100.0*inside/tot:.2f}%')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

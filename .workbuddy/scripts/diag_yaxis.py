# -*- coding: utf-8 -*-
"""确认 buildings.txt 与 positions.txt 的 Y 轴方向差异。"""
import struct, os, re
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')

raw = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
rb = W * 3
a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:rb * H].reshape(H, W, 3)
prov = a[:, :, 2].astype(np.int32) << 16 | a[:, :, 1].astype(np.int32) << 8 | a[:, :, 0].astype(np.int32)

rgb2pid = {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) >= 5:
            try:
                rgb2pid[(int(f2[1]) << 16) | (int(f2[2]) << 8) | int(f2[3])] = int(f2[0])
            except ValueError:
                pass

print('=== buildings.txt 用两种映射的命中率 ===')
for tag, fn in (('row=H-1-z,col=x', lambda z: H - 1 - int(z)), ('row=z,col=x', lambda z: int(z))):
    hit = tot = 0
    for ln in open(os.path.join(MAP, 'buildings.txt'), encoding='utf-8', errors='replace'):
        f = ln.strip().split(';')
        if len(f) < 6:
            continue
        try:
            pid = int(f[0]); x = float(f[2]); z = float(f[4])
        except ValueError:
            continue
        r = fn(z); c = int(x)
        tot += 1
        if 0 <= c < W and 0 <= r < H and rgb2pid.get(int(prov[r, c])) == pid:
            hit += 1
    print(f'   {tag:<20} {hit:,}/{tot:,} = {100.0*hit/tot:.2f}%')

print()
print('=== positions.txt 用两种映射的命中率 ===')
pos = {}
cur = None; seen = False
for ln in open(os.path.join(MAP, 'positions.txt'), 'rb'):
    s = ln.decode('ascii', 'replace').strip()
    m = re.match(r'^(\d+)=\{$', s)
    if m:
        cur = int(m.group(1)); seen = False; continue
    if cur is not None and not seen:
        mm = re.match(r'^([\d.]+)\s+([\d.]+)\s+([\d.]+)$', s)
        if mm:
            pos[cur] = (float(mm.group(1)), float(mm.group(3))); seen = True

for tag, fn in (('row=H-1-z,col=x', lambda z: H - 1 - int(z)), ('row=z,col=x', lambda z: int(z))):
    hit = 0
    for pid, (x, z) in pos.items():
        r = fn(z); c = int(x)
        if 0 <= c < W and 0 <= r < H and rgb2pid.get(int(prov[r, c])) == pid:
            hit += 1
    print(f'   {tag:<20} {hit:,}/{len(pos):,} = {100.0*hit/len(pos):.2f}%')

# -*- coding: utf-8 -*-
"""验证 provinces.bmp 读取是否正确：用 positions 坐标反查，并交叉 definition.csv。"""
import struct, os, re
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
raw = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
bpp = struct.unpack_from('<H', raw, 28)[0]
ncol = struct.unpack_from('<I', raw, 46)[0]
print(f'off={o} W={W} H={H} bpp={bpp} ncol={ncol} size={len(raw)} 期望={54+W*H*3}')

# 24bpp BGR, 行 padding 到 4 字节
rowbytes = W * 3
pad = (4 - rowbytes % 4) % 4
print(f'rowbytes={rowbytes} pad={pad} 总={54+(rowbytes+pad)*H}')

# 用 numpy 直接切
arr = np.frombuffer(raw, dtype=np.uint8, offset=o)
arr = arr[:(rowbytes + pad) * H].reshape(H, rowbytes + pad)
arr = arr[:, :rowbytes].reshape(H, W, 3)
# BGR -> 0xRRGGBB
rgb = arr[:, :, 2].astype(np.int32) << 16 | arr[:, :, 1].astype(np.int32) << 8 | arr[:, :, 0].astype(np.int32)

rgb2pid = {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) < 5:
            continue
        try:
            rgb2pid[(int(f2[1]) << 16) | (int(f2[2]) << 8) | int(f2[3])] = int(f2[0])
        except ValueError:
            pass

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
            pos[cur] = (float(mm.group(1)), float(mm.group(2)), float(mm.group(3))); seen = True

print(f'\n省721 位置: {pos.get(721)}')
for pid in (1, 10, 721, 729, 2467, 4676):
    if pid in pos:
        x, y, z = pos[pid]
        print(f'\n省{pid}: x={x:.2f} z={z:.2f}')
        # 几种映射
        for nm, (r0, c0) in {
            'row=H-1-z,col=x': (H - 1 - int(z), int(x)),
            'row=z,col=x': (int(z), int(x)),
        }.items():
            v = rgb[r0, c0]
            print(f'   {nm:<20} -> rgb={v:#08x} pid={rgb2pid.get(int(v))}')

# 检查 map/positions.txt 某条的完整块
print('\n=== positions.txt 省1 块 ===')
lns = open(os.path.join(MAP, 'positions.txt'), 'rb').read().split(b'\n')
for i, ln in enumerate(lns):
    if ln.strip() == b'1={':
        for j in range(i, i + 10):
            print('   ', lns[j].decode('ascii', 'replace').rstrip())
        break
print('=== positions.txt 省721 块 ===')
for i, ln in enumerate(lns):
    if ln.strip() == b'721={':
        for j in range(i, i + 10):
            print('   ', lns[j].decode('ascii', 'replace').rstrip())
        break

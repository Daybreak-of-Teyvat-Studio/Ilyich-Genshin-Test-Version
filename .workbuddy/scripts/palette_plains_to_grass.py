# -*- coding: utf-8 -*-
"""把 terrain.bmp 调色板里索引 0（平原）的显示色从橙 (255,129,66) 改为草绿 (89,199,85)。
只动调色板 3 个字节，像素区一字不改。产出补丁文件与前后对照预览。"""
import struct, os, hashlib, shutil, collections
import numpy as np
from PIL import Image

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MAP = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'map')
SRC = os.path.join(MAP, 'terrain.bmp')
WB = os.path.join(ROOT, '.workbuddy', 'terrain_05_palette.bmp')
BK = os.path.join(ROOT, '.workbuddy', 'backup_20260924_1550')
PREV = os.path.join(ROOT, '.workbuddy', 'preview')
REP = os.path.join(ROOT, '.workbuddy', 'report_terrain05.txt')
os.makedirs(PREV, exist_ok=True)
os.makedirs(BK, exist_ok=True)

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()

NEW = (89, 199, 85)

# ---------- 0. 备份 ----------
shutil.copy2(SRC, os.path.join(BK, 'terrain.bmp'))
P('=== 0. 备份 ===')
P(f'  {os.path.join(BK, "terrain.bmp")}  md5={md5(os.path.join(BK, "terrain.bmp"))}')

# ---------- 1. 读源文件 ----------
raw = bytearray(open(SRC, 'rb').read())
off = struct.unpack_from('<I', raw, 10)[0]
w, h = struct.unpack_from('<ii', raw, 18)
dib = struct.unpack_from('<I', raw, 14)[0]
bpp = struct.unpack_from('<HH', raw, 26)[1]
cu = struct.unpack_from('<I', raw, 46)[0]
pal_off = 14 + dib
n = cu or (off - 14 - dib) // 4

P('')
P('=== 1. 源文件 ===')
P(f'  {SRC}')
P(f'  {len(raw):,} B   off={off}   dib={dib}   bpp={bpp}   clrUsed={cu}   {w}x{h}')
P(f'  调色板 {pal_off}..{pal_off + n * 4}，{n} 项，结束应与 off={off} 相等')
assert pal_off + n * 4 == off, '调色板长度与像素偏移对不上'
assert bpp == 8, f'位深不是 8，实际 {bpp}'

old0 = tuple(raw[pal_off:pal_off + 3][::-1])
assert old0 == (255, 129, 66), f'索引0 原色不是橙 (255,129,66)，实际 {old0}'
P(f'  索引 0 原色 = {old0}')

PAL_OLD = [tuple(raw[pal_off + i * 4: pal_off + i * 4 + 3][::-1]) for i in range(n)]
P('  改前调色板:')
for i, c in enumerate(PAL_OLD):
    P(f'    [{i:2d}] {c}')

# ---------- 2. 只改索引 0 的 3 个字节 ----------
before = bytes(raw)
raw[pal_off + 0] = NEW[2]   # B
raw[pal_off + 1] = NEW[1]   # G
raw[pal_off + 2] = NEW[0]   # R
after = bytes(raw)

diff = [i for i in range(len(before)) if before[i] != after[i]]
P('')
P('=== 2. 字节级改动 ===')
P(f'  改动字节数 = {len(diff)}   位置 = {diff}   (色槽 0 位于 {pal_off}..{pal_off+3})')
assert diff == [pal_off, pal_off + 1, pal_off + 2], diff
assert before[off:] == after[off:], '像素区被改动了！'
P(f'  像素区 {off}..{len(before)} 共 {len(before)-off:,} 字节逐字节一致 = True')
P(f'  文件长度不变 = {len(before) == len(after)}  ({len(before):,} B)')

# ---------- 3. 写出 ----------
open(WB, 'wb').write(after)
r = bytearray(open(WB, 'rb').read())
off2 = struct.unpack_from('<I', r, 10)[0]
cu2 = struct.unpack_from('<I', r, 46)[0]
new0 = tuple(r[pal_off:pal_off + 3][::-1])
P('')
P('=== 3. 写出与回读 ===')
P(f'  {WB}  {os.path.getsize(WB):,} B')
P(f'  回读 off={off2} clrUsed={cu2} 索引0={new0}  长度一致={os.path.getsize(WB) == len(before)}')
assert new0 == NEW and off2 == off and cu2 == cu

# ---------- 4. 索引直方图 ----------
pix_old = np.frombuffer(before[off:off + w * h], dtype=np.uint8)
pix_new = np.frombuffer(after[off:off + w * h], dtype=np.uint8)
h_old = collections.Counter(pix_old.tolist())
h_new = collections.Counter(pix_new.tolist())
P('')
P('=== 4. 索引直方图 ===')
P(f'  改前 {sorted(h_old.items())}')
P(f'  改后 {sorted(h_new.items())}')
P(f'  完全一致 = {h_old == h_new}；未定义索引 = {sorted(set(h_new) - {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,27,31})}')

pal_new = [tuple(after[pal_off + i * 4: pal_off + i * 4 + 3][::-1]) for i in range(n)]
P('  改后调色板:')
for i, c in enumerate(pal_new):
    tag = ''
    if i == 0:
        tag = '   <- 平原，本次改动'
    if i == 1:
        tag = '   <- 森林，0 像素'
    P(f'    [{i:2d}] {c}{tag}')
dup = [i for i in range(n) if i != 0 and pal_new[i] == NEW]
P(f'  与色槽0 同色的其他色槽 = {dup}')

# ---------- 5. 预览 ----------
im = Image.open(SRC)
assert im.mode == 'P' and im.size == (w, h), (im.mode, im.size)

def flat(pal):
    f = []
    for i in range(256):
        c = pal[i] if i < len(pal) else (0, 0, 0)
        f += list(c)
    return f

before_img = im.convert('RGB')
after_im = im.copy()
after_im.putpalette(flat(pal_new))
after_img = after_im.convert('RGB')

a = np.array(before_img); b = np.array(after_img)
changed = int((a != b).any(axis=2).sum())
P('')
P('=== 5. 观感变化 ===')
P(f'  显示色变化的像素 = {changed:,}  (应等于索引0 像素数 {h_new.get(0,0):,})')
P(f'  其余 {a.shape[0]*a.shape[1]-changed:,} 像素显示色不变')

small_b = before_img.resize((1024, 512), Image.NEAREST)
small_a = after_img.resize((1024, 512), Image.NEAREST)
small_a.save(os.path.join(PREV, 'terrain_05_preview.png'))

cmp_im = Image.new('RGB', (1024, 1044), (255, 255, 255))
cmp_im.paste(small_b, (0, 8))
cmp_im.paste(small_a, (0, 532))
cmp_im.save(os.path.join(PREV, 'terrain_05_before_after.png'))

idxmap = np.array(im)
best, bestn = (0, 0), -1
for oy in range(0, h - 256, 256):
    for ox in range(0, w - 256, 256):
        c = int((idxmap[oy:oy + 256, ox:ox + 256] == 0).sum())
        if c > bestn:
            bestn, best = c, (ox, oy)
ox, oy = best
P(f'  平原最密 256x256 区块 左上角=({ox},{oy})  平原 {bestn:,}/{256*256}')
za = after_img.crop((ox, oy, ox + 256, oy + 256)).resize((512, 512), Image.NEAREST)
zb = before_img.crop((ox, oy, ox + 256, oy + 256)).resize((512, 512), Image.NEAREST)
z = Image.new('RGB', (1040, 512), (255, 255, 255))
z.paste(zb, (0, 0)); z.paste(za, (528, 0))
z.save(os.path.join(PREV, 'terrain_05_zoom.png'))

P('')
P('=== 6. 产物 ===')
P(f'  补丁文件 {WB}  md5={md5(WB)}')
P(f'  当前装机 {SRC}  md5={md5(SRC)}（替换前）')
P(f'  备份     {os.path.join(BK, "terrain.bmp")}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

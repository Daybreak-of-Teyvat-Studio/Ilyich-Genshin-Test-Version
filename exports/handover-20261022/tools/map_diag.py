# -*- coding: utf-8 -*-
"""map_diag.py —— 地图文件级诊断
1) 原版 definition.csv 省数（对照 13414 之谜）
2) mod provinces.bmp 文件头/位深/颜色数 vs definition.csv 颜色配对
3) definition.csv 行尾/最大 id/异常行
4) 10-04 转储 exception 对比"""
import os, sys, re

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
STEAM = r'F:\Steam\steamapps\common\Hearts of Iron IV'

print('=== 1. 原版 definition.csv ===')
p = os.path.join(STEAM, 'map', 'definition.csv')
if os.path.exists(p):
    mx = 0
    n = 0
    for l in open(p, encoding='utf-8-sig', errors='replace'):
        a = l.split(';')
        if a[0].strip().isdigit():
            n += 1
            mx = max(mx, int(a[0]))
    print(f'行数 {n}，最大 id {mx}')
else:
    print('找不到', p)

print()
print('=== 2. mod provinces.bmp 文件头 ===')
p = os.path.join(R, 'map', 'provinces.bmp')
raw = open(p, 'rb').read(70)
print('前 2 字节:', raw[:2], '（BM=标准 BMP）')
if raw[:2] == b'BM':
    import struct
    size = struct.unpack('<I', raw[2:6])[0]
    off = struct.unpack('<I', raw[10:14])[0]
    dib = struct.unpack('<I', raw[14:18])[0]
    w, h = struct.unpack('<ii', raw[18:26])
    planes, bpp = struct.unpack('<HH', raw[26:30])
    print(f'文件头: 声明大小 {size}，像素偏移 {off}，DIB {dib}，{w}x{h}，{bpp}bpp')
    print(f'实际文件大小: {os.path.getsize(p)}')

print()
print('=== 3. mod definition.csv ===')
p = os.path.join(R, 'map', 'definition.csv')
raw = open(p, 'rb').read()
print('行尾: CRLF' if b'\r\n' in raw else '行尾: LF')
print('BOM:', raw[:3] == b'\xef\xbb\xbf')
mx = n = 0
bad = []
for i, l in enumerate(raw.decode('utf-8-sig', errors='replace').splitlines(), 1):
    a = l.split(';')
    if not a or not a[0].strip():
        continue
    if not a[0].strip().isdigit():
        bad.append((i, l[:60]))
        continue
    n += 1
    mx = max(mx, int(a[0]))
print(f'数据行 {n}，最大 id {mx}，异常行 {bad[:5]}')
print('前 3 行:', raw.decode('utf-8-sig', errors='replace').splitlines()[:3])
print('后 3 行:', raw.decode('utf-8-sig', errors='replace').splitlines()[-3:])

print()
print('=== 4. 10-04 转储对比 ===')
CD = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\crashes\hoi4_20261004_214707'
p = os.path.join(CD, 'meta.yml')
if os.path.exists(p):
    t = open(p, encoding='utf-8', errors='replace').read()
    for line in t.splitlines():
        if any(k in line for k in ('AppVersion', 'IsMapInGoodState', 'Mods', 'HasMods')):
            print(' ', line.strip())

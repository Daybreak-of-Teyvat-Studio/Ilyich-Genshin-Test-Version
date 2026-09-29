# -*- coding: utf-8 -*-
"""对 14 个"落海"胜利点省做深挖：
 1) 它们在 definition.csv 里的类型；
 2) 它们的真实像素质心（从 provinces.bmp 算）；
 3) 它们是否出现在某个州（history/states）的 provinces 列表里；
 4) 给出「应该改成什么坐标」。
"""
import struct, os, re, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
MAP = os.path.join(MOD, 'map')
REP = os.path.join(ROOT, '.workbuddy', 'report_bad_vp.txt')

BAD = [222, 674, 688, 774, 860, 1269, 1752, 2435, 2473, 3055, 3939, 4680, 4689, 4691]

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

raw = open(os.path.join(MAP, 'provinces.bmp'), 'rb').read()
o = struct.unpack_from('<I', raw, 10)[0]
W, H = struct.unpack_from('<ii', raw, 18)
rb = W * 3
a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:rb * H].reshape(H, W, 3)
prov = (a[:, :, 2].astype(np.int32) << 16) | (a[:, :, 1].astype(np.int32) << 8) | a[:, :, 0].astype(np.int32)
rgb2pid, pid_rgb, pid_type = {}, {}, {}
with open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace') as f:
    for ln in f:
        f2 = ln.strip().split(';')
        if len(f2) >= 5:
            try:
                rgb2pid[(int(f2[1]) << 16) | (int(f2[2]) << 8) | int(f2[3])] = int(f2[0])
                pid_rgb[int(f2[0])] = (int(f2[1]), int(f2[2]), int(f2[3]))
                pid_type[int(f2[0])] = f2[4]
            except ValueError:
                pass

hmraw = open(os.path.join(MAP, 'heightmap.bmp'), 'rb').read()
ho = struct.unpack_from('<I', hmraw, 10)[0]
hm = np.frombuffer(hmraw, dtype=np.uint8, offset=ho)[:W * H].reshape(H, W)

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

# 每个省的像素质心
P('=== 14 个落海省的真相 ===')
P(f'{"pid":<8}{"definition类型":<12}{"RGB":<16}{"像素数":>9}{"像素质心(col,row)":>26}{"现positions":>22}{"该点h":>7}')
fixes = {}
for pid in BAD:
    rgb = pid_rgb.get(pid)
    if rgb is None:
        P(f'{pid:<8}(definition 里没有)')
        continue
    key = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
    mask = prov == key
    n = int(mask.sum())
    if n:
        ys, xs = np.where(mask)
        cc, cr = float(xs.mean()), float(ys.mean())
        hmin, hmax = int(hm[mask].min()), int(hm[mask].max())
        hmed = int(np.median(hm[mask]))
        cen = f'({cc:.1f}, {cr:.1f})'
    else:
        cc = cr = None; hmin = hmax = hmed = None
        cen = '(无像素)'
    p = pos.get(pid)
    hv = int(hm[int(p[1]), int(p[0])]) if p else None
    P(f'{pid:<8}{pid_type.get(pid,"?"):<12}{str(rgb):<16}{n:>9,}{cen:>26}{str(p):>22}{hv:>7}')
    if n:
        tgt = (round(cc, 3), round(cr, 3))
        # 质心处 h
        th = int(hm[int(cr), int(cc)])
        fixes[pid] = (p, tgt, th, n, f'h范围 {hmin}~{hmax} 中位 {hmed}')

P('')
P('=== 建议修正（positions 坐标 -> 该省像素质心）===')
for pid, (p, tgt, th, n, rng) in fixes.items():
    P(f'   省{pid:<6} 现 ({p[0]:.3f}, {p[1]:.3f}) -> 建议 ({tgt[0]:.3f}, {tgt[1]:.3f})   质心 h={th} ({rng})  像素 {n:,}')

# 这些省是否被某个州引用
P('')
P('=== 这些省在州文件里的引用 ===')
ref = collections.defaultdict(list)
for dp, _, fs in os.walk(os.path.join(MOD, 'history', 'states')):
    for fn in fs:
        if not fn.endswith('.txt'):
            continue
        txt = open(os.path.join(dp, fn), encoding='utf-8', errors='replace').read()
        for pid in BAD:
            if re.search(r'(?<![\d])' + str(pid) + r'(?![\d])', txt):
                ref[pid].append(fn)
for pid in BAD:
    P(f'   省{pid:<6} 出现在: {ref.get(pid, ["(无)"])}')

# 这些省在 definition.csv 的 land/ocean 附近
P('')
P('=== 这些省在 definition.csv 的邻居行（前后各 2）===')
lines = open(os.path.join(MAP, 'definition.csv'), encoding='utf-8', errors='replace').read().splitlines()
idx = {}
for i, ln in enumerate(lines):
    f2 = ln.strip().split(';')
    if f2 and f2[0].isdigit():
        idx[int(f2[0])] = i
for pid in BAD[:6]:
    i = idx.get(pid)
    if i is None:
        continue
    P(f'   --- 省{pid} 附近 ---')
    for j in range(max(0, i - 2), min(len(lines), i + 3)):
        P('      ' + lines[j])

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

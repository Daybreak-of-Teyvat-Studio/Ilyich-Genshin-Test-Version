# -*- coding: utf-8 -*-
"""
读主写的涂色图，逐省判定归属。

用法：
  python gamma_read_colors.py 涂色图.png|tif [--no-sky]

判定逻辑：
  · 省的真值几何来自 provinces.bmp + definition.csv（与涂色图同一 4096x2048 坐标系）
  · 每个陆地省：取该省像素的**主导填充色**（透明像素视为"未填"）
  · 按颜色分组，输出 颜色 -> 省列表，以及每省置信度
  · 置信度低于阈值的省单独列出，交主写裁决

两种涂色导出方式都支持：
  A) 只导出填充层（带 alpha）—— 未填 = 透明，最稳，推荐
  B) 导出合并图 —— 必须把所有陆地省都填满，否则未填区与地形色混淆
"""
import os, re, sys, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
OUTDIR = os.path.join(ROOT, 'Gamma_地图', '划分结果')
os.makedirs(OUTDIR, exist_ok=True)

args = [a for a in sys.argv[1:] if not a.startswith('--')]
# 天空岛（天理 PRI 的 17 州）默认排除：主写会自己手动修那一块
NO_SKY = '--include-sky' not in sys.argv
if not args:
    print('用法: python gamma_read_colors.py 涂色图.png [--no-sky]'); sys.exit(1)
SRC = args[0]
CONF_MIN = 0.90            # 置信度阈值

# ---------------- 省 / 州几何 ----------------
s2o, s2p = {}, {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2o[sid] = re.search(r'\bowner\s*=\s*(\w+)', t).group(1)
    s2p[sid] = [int(x) for x in re.search(r'provinces = \{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}
sky_states = {s for s, o in s2o.items() if o == 'PRI'}

rgb2id, kind = {}, {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
        kind[int(a[0])] = a[4]

arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
klut = np.zeros(len(uniq), np.uint8)
for i, k in enumerate(uniq):
    k = int(k)
    pid = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
    plut[i] = pid
    klut[i] = 1 if kind.get(pid, 'sea') == 'land' else 0
prov = plut[inv].reshape(H, W)
land = klut[inv].reshape(H, W).astype(bool)
print(f'地图 {W}x{H}，陆地省 {len({int(p) for p in np.unique(prov[land])})} 个')

# ---------------- 读涂色图 ----------------
im = Image.open(SRC)
print(f'涂色图: {SRC}  {im.size} {im.mode}')
if im.size != (W, H):
    print(f'!! 尺寸不符，应为 {W}x{H}，实际 {im.size}，坐标会对不上')
    sys.exit(1)
has_alpha = im.mode in ('RGBA', 'LA') or 'transparency' in im.info
rgba = np.asarray(im.convert('RGBA')).astype(np.int16)
ca = np.asarray(im.convert('RGB')).astype(np.int16)
alpha = rgba[:, :, 3]
filled = alpha > 128 if has_alpha else np.ones((H, W), bool)
if has_alpha:
    print(f'带 alpha：填充像素 {int(filled.sum())} / 陆地像素 {int(land.sum())}')
    # 半透明/羽化像素提示
    semi = int(((alpha > 8) & (alpha <= 128)).sum())
    if semi > land.sum() * 0.01:
        print(f'!! 有 {semi} 个半透明像素（可能是羽化/抗锯齿），建议填充时关掉消除锯齿')

# ---------------- 逐省主导色 ----------------
flat_prov = prov.ravel()
flat_land = land.ravel()
flat_fill = filled.ravel()
col32 = (ca[:, :, 0].astype(np.int32) << 16) | (ca[:, :, 1].astype(np.int32) << 8) | ca[:, :, 2].astype(np.int32)
flat_col = col32.ravel()

order = np.argsort(flat_prov, kind='stable')
sp = flat_prov[order]
s_land = flat_land[order]
s_fill = flat_fill[order]
s_col = flat_col[order]
idx = np.searchsorted(sp, np.arange(int(flat_prov.max()) + 2))

result = {}          # pid -> (hexcolor or None, conf, npix)
for pid in range(1, int(flat_prov.max()) + 1):
    lo, hi = idx[pid], idx[pid + 1]
    if hi <= lo:
        continue
    sl = slice(lo, hi)
    m = s_land[sl]
    if not m.any():
        continue
    cols = s_col[sl][m]
    fl = s_fill[sl][m]
    total = cols.size
    if fl.sum() == 0:
        result[pid] = (None, 0.0, total)
        continue
    cc = collections.Counter(cols[fl].tolist())
    c, n = cc.most_common(1)[0]
    result[pid] = (f'#{c:06X}', n / total, total)

print(f'已判定省 {len(result)} 个')

# ---------------- 按颜色聚合 ----------------
bycol = collections.defaultdict(list)
unfilled = []
for pid, (c, conf, n) in result.items():
    if c is None:
        unfilled.append(pid)
    else:
        bycol[c].append((pid, conf))

print()
print('=' * 60)
print(f'颜色分组（共 {len(bycol)} 种颜色）')
print('=' * 60)
for c, lst in sorted(bycol.items(), key=lambda x: -len(x[1])):
    pids = [p for p, _ in lst]
    states = collections.Counter(p2s[p] for p in pids if p in p2s)
    nstate = len(states)
    low = [p for p, cf in lst if cf < CONF_MIN]
    print(f'  {c}  省 {len(pids):4d}  占 {nstate:3d} 个州'
          + (f'  低置信 {len(low)}' if low else ''))
    if len(bycol) <= 40:
        print(f'       省: {pids[:24]}{" ..." if len(pids) > 24 else ""}')

if unfilled:
    print(f'\n未填色的陆地省 {len(unfilled)} 个: {unfilled[:40]}{" ..." if len(unfilled) > 40 else ""}')

# ---------------- 州的多数归属 + 跨色州 ----------------
print()
print('=' * 60)
print('按现有州汇总（多数色决定归属）')
print('=' * 60)
straddle = []
for s in sorted(s2p):
    if NO_SKY and s in sky_states:
        continue
    cs = collections.Counter()
    for p in s2p[s]:
        c = result.get(p, (None, 0, 0))[0]
        if c:
            cs[c] += 1
    if not cs:
        continue
    if len(cs) > 1:
        straddle.append((s, cs))
print(f'跨色州 {len(straddle)} 个（这些州内的省分了多个颜色，需要后续处理）')
for s, cs in sorted(straddle, key=lambda x: -len(x[1]))[:40]:
    print(f'  state {s:4d} owner {s2o[s]:4s} 省数 {len(s2p[s]):2d}  '
          + '  '.join(f'{c}x{n}' for c, n in cs.most_common()))

# ---------------- 低置信省 ----------------
lowall = [(p, c, cf) for p, (c, cf, n) in result.items() if c and cf < CONF_MIN]
print()
print(f'低置信省（占比 < {CONF_MIN:.0%}）共 {len(lowall)} 个')
for p, c, cf in sorted(lowall, key=lambda x: x[2])[:60]:
    print(f'  province {p:5d} 现属 state {p2s.get(p)}  {c} 占比 {cf:.0%}')

# ---------------- 输出预览：按颜色分组重绘 ----------------
PAL = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (67, 99, 216), (245, 130, 49),
       (145, 30, 180), (66, 212, 244), (240, 50, 230), (191, 239, 69), (250, 190, 212),
       (70, 153, 144), (220, 190, 255), (154, 99, 36), (255, 250, 200), (128, 0, 0)]
out = np.full((H, W, 3), 245, np.uint8)
out[~land] = (225, 232, 240)
cmap = {}
for i, (c, _) in enumerate(sorted(bycol.items(), key=lambda x: -len(x[1]))):
    cmap[c] = PAL[i % len(PAL)]
lut = np.zeros(int(flat_prov.max()) + 2, dtype=np.int32)
for pid, (c, conf, n) in result.items():
    lut[pid] = -1 if c is None else list(cmap).index(c) + 1
per_pix = lut[prov]
for i, c in enumerate(cmap):
    out[per_pix == i + 1] = cmap[c]
out[per_pix == -1] = (255, 0, 0)
Image.fromarray(out, 'RGB').save(os.path.join(OUTDIR, '读色结果_预览.png'))
Image.fromarray(out, 'RGB').resize((2048, 1024), Image.NEAREST).save(
    os.path.join(OUTDIR, '读色结果_预览_半尺寸.png'))
print(f'\n预览已出: {OUTDIR}')

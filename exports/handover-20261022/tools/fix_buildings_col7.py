# -*- coding: utf-8 -*-
"""fix_buildings_col7.py —— 按"第 7 列规则"修复 buildings.txt 声明州
规则与 check_states.py 一致：
  col7=陆省 → col1 = 该省所属州
  col7=海省 + 海军类 → col1 = 吸附省（provinces.bmp 像素/最近陆像素）所属州
只改违规行，其余字节不动；改完用同款算法复验。
"""
import os, re, sys, glob, shutil, datetime, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BP = os.path.join(MOD, 'map', 'buildings.txt')
ST = os.path.join(MOD, 'history', 'states')
DEF = os.path.join(MOD, 'map', 'definition.csv')
NAVAL = {'naval_base_spawn', 'naval_headquarters', 'naval_supply_hub',
         'coastal_bunker', 'floating_harbor'}

# 省 → 州
p2s = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        p2s[int(x)] = sid

# 省类型（land/sea/lake）
kind = {}
for line in open(DEF, encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]

# provinces.bmp 像素 → 省
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
rgb = {}
for line in open(DEF, encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
arr = np.asarray(Image.open(os.path.join(MOD, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
u, inv = np.unique(key, return_inverse=True)
pl = np.zeros(len(u), np.int32)
for i, k in enumerate(u):
    k = int(k)
    pl[i] = rgb.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = pl[inv].reshape(H, W)
lm = np.isin(prov, [q for q, k2 in kind.items() if k2 == 'land'])


def snap(x, y):
    """与 check_states 同款：先试原像素，再螺旋搜最近陆省"""
    if 0 <= y < H and 0 <= x < W and lm[y, x]:
        return int(prov[y, x])
    for r in range(1, 16):
        y0, y1 = max(0, y - r), min(H, y + r + 1)
        x0, x1 = max(0, x - r), min(W, x + r + 1)
        sl = lm[y0:y1, x0:x1]
        if sl.any():
            vals = prov[y0:y1, x0:x1][sl]
            return int(collections.Counter(vals.tolist()).most_common(1)[0][0])
    return None


raw = open(BP, 'rb').read()
nl = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl)
fixed, n = [], 0
for i, l in enumerate(lines):
    f = l.split(';')
    if len(f) != 7 or not f[0].isdigit() or not f[6].isdigit():
        continue
    p7, decl = int(f[6]), int(f[0])
    want = None
    if p7 in p2s and kind.get(p7) == 'land':
        want = p2s[p7]
    elif p7 and kind.get(p7) != 'land' and f[1] in NAVAL:
        y, x = int(round(H - float(f[4]))), int(round(float(f[2])))
        lp = snap(x, y)
        if lp is not None:
            want = p2s.get(lp)
    if want is not None and want != decl:
        f[0] = str(want)
        lines[i] = ';'.join(f)
        fixed.append((f[1], decl, want, p7))
        n += 1

print(f'修复 {n} 行:')
for bt, old, new, p7 in fixed:
    print(f'  {bt}: 州 {old} → {new}（省 {p7}）')
if n:
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bd = os.path.join(ROOT, '.backups', f'bcol7_{stamp}')
    os.makedirs(bd, exist_ok=True)
    shutil.copy2(BP, os.path.join(bd, 'buildings.txt'))
    open(BP, 'wb').write(nl.join(lines).encode('utf-8'))
    print(f'备份: {bd}')

# 复验（同款算法）
bad = 0
for l in open(BP, 'rb').read().decode('utf-8-sig').split(nl):
    f = l.split(';')
    if len(f) != 7 or not f[0].isdigit() or not f[6].isdigit():
        continue
    p7, decl = int(f[6]), int(f[0])
    if p7 in p2s and kind.get(p7) == 'land':
        bad += p2s[p7] != decl
    elif p7 and kind.get(p7) != 'land' and f[1] in NAVAL:
        y, x = int(round(H - float(f[4]))), int(round(float(f[2])))
        lp = snap(x, y)
        bad += lp is not None and p2s.get(lp) != decl
print(f'复验: 第 7 列违规 {bad} 处')

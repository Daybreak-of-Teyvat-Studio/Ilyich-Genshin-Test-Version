# -*- coding: utf-8 -*-
"""
buildings 修复 v2：以「第 7 列省号」为准对齐声明州（游戏的真实判定依据）。
  · 第 7 列 = 陆省 → 第 1 列 = 该省所属州（SL 与省级类同规则）
  · 第 7 列 = 海域省 → 海军类吸附最近陆省定声明州；陆地类 = 水上非法（报告）
顺带修补号漏改的 name 行（123/125 的 DOT_STATE_861/860）。
"""
import os, re, sys, shutil, datetime, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
DRY = '--dry' in sys.argv

kind = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
LAND = {p for p, k in kind.items() if k == 'land'}

s2p, s2o = {}, {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    s2o[sid] = mo.group(1) if mo else None
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}

rgb2id = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)
lmask = np.isin(prov, list(LAND))
_cache = {}


def snap_land(y, x, maxr=15):
    if (y, x) in _cache:
        return _cache[(y, x)]
    res = None
    if 0 <= y < H and 0 <= x < W and lmask[y, x]:
        res = int(prov[y, x])
    else:
        for r in range(1, maxr + 1):
            y0, y1 = max(0, y - r), min(H, y + r + 1)
            x0, x1 = max(0, x - r), min(W, x + r + 1)
            sl = lmask[y0:y1, x0:x1]
            if sl.any():
                vals = prov[y0:y1, x0:x1][sl]
                res = int(collections.Counter(vals.tolist()).most_common(1)[0][0])
                break
    _cache[(y, x)] = res
    return res


NAVAL = {'naval_base_spawn', 'naval_headquarters', 'naval_supply_hub',
         'coastal_bunker', 'floating_harbor'}

raw = open(BP, 'rb').read()
lines = raw.decode('utf-8-sig').split('\r\n')
stats = collections.Counter()
report = []
for i, l in enumerate(lines):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    p7 = int(f[6]) if f[6].isdigit() else 0
    decl = int(f[0])
    if p7 in p2s and kind.get(p7) == 'land':
        want = p2s[p7]
        if decl != want:
            stats['省列陆省-改声明州'] += 1
            if len(report) < 10:
                report.append(f'  {f[1]}: 声明 {decl} → {want}（省列 {p7}）')
            f[0] = str(want)
            lines[i] = ';'.join(f)
    elif p7 and kind.get(p7) != 'land':
        # 水上标记
        y, x = int(round(H - float(f[4]))), int(round(float(f[2])))
        lp = snap_land(y, x)
        if lp is None:
            stats['水上无法吸附'] += 1
            continue
        if f[1] in NAVAL:
            want = p2s.get(lp)
            if want and decl != want:
                stats['水面海军类-按吸附改声明州'] += 1
                f[0] = str(want)
                lines[i] = ';'.join(f)
        else:
            stats['陆类标记在水上-非法'] += 1
            if len(report) < 10:
                report.append(f'  !! {f[1]} 省列 {p7}(海) 声明 {decl}——水上非法')

print('=== 扫描结果 ===')
for k, v in stats.most_common():
    print(f'  {k}: {v}')
for r in report:
    print(r)

if DRY:
    print('[DRY] 未写盘')
    sys.exit(0)

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bdir = os.path.join(ROOT, '.backups', 'col7_fix_' + stamp)
os.makedirs(bdir, exist_ok=True)
shutil.copy2(BP, os.path.join(bdir, 'buildings.txt'))
open(BP, 'w', encoding='utf-8', newline='').write('\r\n'.join(lines))
print(f'\nbuildings.txt 已写入，备份 {bdir}')

# 终验（按游戏规则：第 7 列省归属 vs 声明州）
mism = 0
for l in open(BP, encoding='utf-8-sig', newline='').read().split('\r\n'):
    f = l.split(';')
    if len(f) != 7:
        continue
    p7 = int(f[6]) if f[6].isdigit() else 0
    decl = int(f[0])
    if p7 in p2s and kind.get(p7) == 'land':
        if p2s[p7] != decl:
            mism += 1
    elif p7 and kind.get(p7) != 'land':
        y, x = int(round(H - float(f[4]))), int(round(float(f[2])))
        lp = snap_land(y, x)
        if lp and f[1] in NAVAL and p2s.get(lp) != decl:
            mism += 1
print(f'终验: 按游戏规则不符 {mism}（应 0）')

# ---- name 行修复（补号漏改） ----
print('\n=== 补号 name 行修复 ===')
for sid, oldk in ((123, 'DOT_STATE_861'), (125, 'DOT_STATE_860')):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    if not os.path.exists(fp):
        continue
    t = open(fp, encoding='utf-8-sig', newline='').read()
    t2 = re.sub(r'(\bname\s*=\s*")' + oldk + r'(")', rf'\g<1>DOT_STATE_{sid}\g<2>', t, count=1)
    if t2 != t:
        shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
        with open(fp, 'w', encoding='utf-8', newline='') as fh:
            fh.write(t2)
        print(f'  state {sid}: name {oldk} → DOT_STATE_{sid}')
    else:
        print(f'  state {sid}: name 已正确')

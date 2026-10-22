# -*- coding: utf-8 -*-
"""
buildings.txt 一键综合重整（从合并后备份恢复 → 游戏真实规则全对齐）：
  规则（实测确认）：
  · naval 五类（naval_base_spawn/naval_headquarters/naval_supply_hub/coastal_bunker/floating_harbor）
    标记画在水上：声明州 = 标记吸附最近陆地省的所属州（第 7 列若是海域省照吸附）
  · 其余类（陆上建筑）：声明州 = 标记坐标像素所在省的所属州（第 7 列多为 0，不参与判定）
  · 州级生成点 SL：每个陆州恰好 7×1 + anti_air×3；海州 0 条
  · 所有声明州必须是当前存在的州
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
GOOD = os.path.join(ROOT, '.backups', 'map_buildings_20260929_191528', 'buildings.txt')
SL = {'air_base': 1, 'fuel_silo': 1, 'radar_station': 1, 'nuclear_reactor_spawn': 1,
      'rocket_site_spawn': 1, 'synthetic_refinery': 1, 'stronghold_network': 1,
      'anti_air_building': 3}
NAVAL = {'naval_base_spawn', 'naval_headquarters', 'naval_supply_hub',
         'coastal_bunker', 'floating_harbor'}
rng = __import__('random').Random(42)

# 州/省数据
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

kind = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
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
lmask = np.isin(prov, [p for p, k in kind.items() if k == 'land'])
POS = {}
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)',
                     open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig',
                          errors='replace').read()):
    POS[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))

_cache = {}
def snap(y, x):
    if (y, x) in _cache:
        return _cache[(y, x)]
    r = None
    if 0 <= y < H and 0 <= x < W and lmask[y, x]:
        r = int(prov[y, x])
    else:
        for rr in range(1, 16):
            y0, y1 = max(0, y - rr), min(H, y + rr + 1)
            x0, x1 = max(0, x - rr), min(W, x + rr + 1)
            sl = lmask[y0:y1, x0:x1]
            if sl.any():
                vals = prov[y0:y1, x0:x1][sl]
                r = int(collections.Counter(vals.tolist()).most_common(1)[0][0])
                break
    _cache[(y, x)] = r
    return r

def game_state(f):
    """游戏判定：该条目应属的州"""
    if f[1] in NAVAL:
        p7 = int(f[6]) if f[6].isdigit() else 0
        if p7 and kind.get(p7) == 'land':
            return p2s.get(p7)
    x, z = float(f[2]), float(f[4])
    lp = snap(int(round(H - z)), int(round(x)))
    return p2s.get(lp) if lp else None

# ---------- 1. 从合并后备份恢复 ----------
shutil.copy2(GOOD, BP)
print(f'① 已从 {GOOD} 恢复 buildings.txt')

# ---------- 2. 第 1 列全对齐（游戏规则） ----------
raw = open(BP, 'rb').read()
nl = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl)
n_align = 0
kept = []
for l in lines:
    f = l.split(';')
    if len(f) != 7:
        kept.append(l)
        continue
    want = game_state(f)
    if want is None:
        # 无法判定的条目（标记在外海深处的海军类）→ 保留原声明
        kept.append(l)
        continue
    if int(f[0]) != want:
        f[0] = str(want)
        l = ';'.join(f)
        n_align += 1
    kept.append(l)
print(f'② 第 1 列按游戏规则对齐: {n_align} 条')

# ---------- 3. SL 标准配置对齐 ----------
out, cur = [], collections.defaultdict(lambda: collections.defaultdict(int))
for l in kept:
    f = l.split(';')
    if len(f) == 7 and f[1] in SL:
        cur[f[1]][int(f[0])] += 1
        if int(f[0]) in s2o and s2o[int(f[0])] is None:
            continue                      # 海州 SL → 删
        if int(f[0]) not in s2p:
            continue                      # 声明不存在的州 → 删
    out.append(l)
# 补缺：每陆州 7+3
TMPL = {}
gb = open(GOOD, encoding='utf-8-sig', newline='').read().split('\n')
for l in gb:
    f = l.split(';')
    if len(f) == 7 and f[1] in SL and f[1] not in TMPL:
        TMPL[f[1]] = f
added = 0
appends = []
for st in sorted(s2p):
    if s2o.get(st) is None:
        continue                          # 海州不放
    land = [p for p in s2p[st] if p in POS]
    if not land:
        continue
    for bt, want in SL.items():
        have = cur[bt].get(st, 0)
        for k in range(max(0, want - have)):
            f = list(TMPL[bt])
            px, py, pz = POS[land[(hash((st, bt, k))) % len(land)]]
            f[0] = str(st)
            f[2], f[3], f[4] = f'{px:.2f}', f'{py:.2f}', f'{pz:.2f}'
            appends.append(';'.join(f))
            added += 1
out = out + appends
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bdir = os.path.join(ROOT, '.backups', 'buildings_rebuild_full_' + stamp)
os.makedirs(bdir, exist_ok=True)
shutil.copy2(BP, os.path.join(bdir, 'buildings_before.txt'))
open(BP, 'w', encoding='utf-8', newline='').write(nl.join(out))
print(f'③ SL 标准配置: 补 {added} 条；海州/无效条目已剔除；备份 {bdir}')

# ---------- 4. 终验 ----------
after = collections.defaultdict(lambda: collections.defaultdict(int))
mism = 0
for l in open(BP, encoding='utf-8-sig', newline='').read().split(nl):
    f = l.split(';')
    if len(f) != 7:
        continue
    if f[1] in SL:
        after[f[1]][int(f[0])] += 1
    want = game_state(f)
    if want is not None and int(f[0]) != want:
        mism += 1
bad = 0
for bt in SL:
    for st in s2p:
        want = 0 if s2o.get(st) is None else SL[bt]
        if after[bt].get(st, 0) != want:
            bad += 1
            if bad <= 5:
                print(f'  ! {bt} state {st}: {after[bt].get(st, 0)} ≠ {want}')
print(f'终验: 游戏规则不符 {mism}（应 0）；SL 每陆州 7+3 不符 {bad}（应 0）')

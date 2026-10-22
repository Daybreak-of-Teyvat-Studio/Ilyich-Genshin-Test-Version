# -*- coding: utf-8 -*-
"""
飞地清理 v2：处理「无 4 邻域陆邻州」的离岸碎块。
规则：找到该块最近的陆地省（含任何州）
  · 若该最邻近省属同一州 → 不改（两省隔细水道的合法小岛州）
  · 否则 → 该块并入最近陆省所属州
移动时同步携带：省级建筑块、胜利点。
用法：python fix_enclaves2.py [--dry]
"""
import os, re, sys, collections, datetime, shutil
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
DRY = '--dry' in sys.argv
FAR = 12
MAXR = 30

kind = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
LAND = {p for p, k in kind.items() if k == 'land'}

s2p, s2o, raw = {}, {}, {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    s2o[sid] = mo.group(1) if mo else None
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
    raw[sid] = t
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

src = np.where(lmask, prov, 0)
adj2 = collections.defaultdict(set)
for r in range(3):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if r == 0 and not (dx or dy):
                continue
            a_ = src[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)]
            b_ = src[max(0, dy):H - max(0, -dy), max(0, dx):W - max(0, -dx)]
            m = (a_ != b_) & (a_ > 0) & (b_ > 0)
            for x, y in zip(a_[m].tolist(), b_[m].tolist()):
                if x != y:
                    adj2[x].add(y)
                    adj2[y].add(x)

flat = prov.ravel()
npx = np.bincount(flat, minlength=int(prov.max()) + 2)
gx = np.tile(np.arange(W, dtype=np.float64), H)
gy = np.repeat(np.arange(H, dtype=np.float64), W)
cx = np.bincount(flat, weights=gx, minlength=len(npx)) / np.maximum(npx, 1)
cy = np.bincount(flat, weights=gy, minlength=len(npx)) / np.maximum(npx, 1)


def comps(pset, A):
    ps, seen, out = set(pset), set(), []
    for p in ps:
        if p in seen:
            continue
        blk, q = [], [p]
        seen.add(p)
        while q:
            u = q.pop()
            blk.append(u)
            for v in A[u]:
                if v in ps and v not in seen:
                    seen.add(v)
                    q.append(v)
        out.append(sorted(blk))
    return sorted(out, key=len, reverse=True)


def nearest_land(p, skip):
    """最近的陆地省（排除 skip 集合；跳过自身）"""
    yy, xx = np.nonzero(prov == p)
    if len(yy) == 0:
        return None, -1
    y0, y1, x0, x1 = yy.min(), yy.max(), xx.min(), xx.max()
    for R in range(1, MAXR):
        sy0, sy1 = max(0, y0 - R), min(H, y1 + R + 1)
        sx0, sx1 = max(0, x0 - R), min(W, x1 + R + 1)
        sub = prov[sy0:sy1, sx0:sx1]
        sub = sub[lmask[sy0:sy1, sx0:sx1]]
        cand = sub[(sub != p)]
        if cand.size:
            vals, cnts = np.unique(cand, return_counts=True)
            # 排除 skip 里的省（同州主体省）
            order = np.argsort(-cnts)
            for i in order:
                q = int(vals[i])
                if q not in skip:
                    return q, R
            return int(vals[order[0]]), R
    return None, -1


# 找出所有孤立块
plan, skip_noop = [], []
for sid, ps in sorted(s2p.items()):
    lps = [p for p in ps if p in LAND]
    if len(lps) < 2:
        continue
    c = comps(lps, adj2)
    if len(c) == 1:
        continue
    main = c[0]
    for blk in c[1:]:
        d = min(np.hypot(cx[p] - cx[q], cy[p] - cy[q]) for p in blk for q in main)
        if d <= FAR:
            continue
        tgt = None
        for p in blk:
            q, R = nearest_land(p, skip=set(blk) | set(main))
            if q:
                tgt = p2s.get(q)
                break
        if tgt is None or tgt == sid:
            skip_noop.append((sid, blk, round(d), tgt))
        else:
            plan.append((sid, s2o.get(sid), blk, round(d), tgt, s2o.get(tgt)))

print(f'=== 拟修飞地 {len(plan)} 处 ===')
for sid, tag, blk, d, tgt, ttag in plan:
    print(f'  state {sid}({tag}) 的省 {blk}（距主体 {d}px）→ state {tgt}({ttag})'
          + ('   ⚠ 国家变更' if tag != ttag else ''))
print(f'\n=== 无需改（最近陆省属本州）{len(skip_noop)} 处 ===')
for sid, blk, d, tgt in skip_noop:
    print(f'  state {sid} 的省 {blk}（距主体 {d}px，最近陆省仍属本州）')

if DRY or not plan:
    print('\n[DRY / 未写盘]')
    sys.exit(0)

bdir = os.path.join(ROOT, '.backups', 'enclave2_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
touched = set()
for sid, tag, blk, d, tgt, ttag in plan:
    for p in blk:
        if p in s2p[sid]:
            s2p[sid].remove(p)
        if p not in s2p[tgt]:
            s2p[tgt].append(p)
    touched.add(sid)
    touched.add(tgt)
for sid in sorted(touched):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = re.sub(r'(provinces = \{\r\n\t\t)[^\r\n]*(\r\n\t\})',
               lambda m: f'{m.group(1)}{" ".join(map(str, sorted(s2p[sid])))}{m.group(2)}', raw[sid])
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)
print(f'\n已写入 {len(touched)} 个州文件，备份 {bdir}')

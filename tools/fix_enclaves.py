# -*- coding: utf-8 -*-
"""
飞地清理：全图找出「州内有与主体不接壤的省块」，把它们并入地理相邻的州。
  · 判定：2px 桥接口径下的连通分量 > 1，非主体块距主体 > 12px
  · 目标州：与该块陆上边界最长的邻州（排除本州）
  · 若该块四面环海（无陆邻州）→ 单列报告，不自动处理
用法：python fix_enclaves.py [--dry]
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

kind = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
land_ids = {p for p, k in kind.items() if k == 'land'}

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
p2s = {}
for s, ps in s2p.items():
    for p in ps:
        p2s.setdefault(p, set()).add(s)

# 邻接（4 邻域给边界长度；2px 给连通性）
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
src = np.where(np.isin(prov, list(land_ids)), prov, 0)
adj4, adj2, bd = collections.defaultdict(set), collections.defaultdict(set), collections.Counter()
for r in range(3):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if r == 0 and not (dx or dy):
                continue
            a_ = src[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)]
            b_ = src[max(0, dy):H - max(0, -dy), max(0, dx):W - max(0, -dx)]
            m = (a_ != b_) & (a_ > 0) & (b_ > 0)
            for x, y in zip(a_[m].tolist(), b_[m].tolist()):
                if x == y:
                    continue
                if r == 0:
                    adj4[x].add(y)
                    adj4[y].add(x)
                    bd[(min(x, y), max(x, y))] += 1
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


def border_with(block, other_states):
    """块与某些州的 4 邻域边界像素数"""
    cnt = collections.Counter()
    for p in block:
        for q in adj4[p]:
            for s in other_states.get(q, ()):
                cnt[s] += bd[(min(p, q), max(p, q))]
    return cnt


plan, islands = [], []
for sid, ps in sorted(s2p.items()):
    lps = [p for p in ps if p in land_ids]
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
        nb = border_with(blk, {k: v for k, v in p2s.items() if sid not in v})
        nb.pop(sid, None)
        if nb:
            tgt, bn = nb.most_common(1)[0]
            plan.append((sid, s2o.get(sid), blk, round(d), tgt, s2o.get(tgt), bn, sorted(nb.items(), key=lambda x: -x[1])[:3]))
        else:
            islands.append((sid, s2o.get(sid), blk, round(d)))

print(f'=== 需修的飞地：{len(plan)} 处 ===')
for sid, tag, blk, d, tgt, ttag, bn, top in plan:
    print(f'  state {sid}({tag}) 的 {len(blk)} 省 {blk}（距主体 {d}px）→ 并入 state {tgt}({ttag})，边界 {bn}px；候选 {top}')
print()
print(f'=== 四面环海、无陆邻州的孤立块：{len(islands)} 处 ===')
for sid, tag, blk, d in islands:
    print(f'  state {sid}({tag}) 的 {len(blk)} 省 {blk}（距主体 {d}px）—— 需你决定（可单列为 1 省州）')

if DRY or not plan:
    print('\n[DRY / 无修改]')
    sys.exit(0)

# 应用
bdir = os.path.join(ROOT, '.backups', 'enclave_fix_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
apply_map = {}
for sid, tag, blk, d, tgt, ttag, bn, top in plan:
    for p in blk:
        apply_map[p] = tgt
        s2p[sid].remove(p)
    s2p[tgt] = s2p[tgt] + blk
touched = set()
for sid, tag, blk, d, tgt, ttag, bn, top in plan:
    touched.add(sid)
    touched.add(tgt)
for sid in sorted(touched):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = raw[sid]
    t = re.sub(r'(provinces = \{\r\n\t\t)[^\r\n]*(\r\n\t\})',
               lambda m: f'{m.group(1)}{" ".join(map(str, sorted(s2p[sid])))}{m.group(2)}', t)
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)
print(f'\n已修 {len(plan)} 处飞地，涉及 {len(touched)} 个州文件，备份 {bdir}')
print('省级建筑块/胜利点若随省移动，请再跑 buildings 同步')

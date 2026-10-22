# -*- coding: utf-8 -*-
"""
飞地判定 v3（按真实像素缝隙）：
  对每个与主体分离的省块：
    gap_own   = 到「本州其他省」的最小像素距离
    gap_other = 到「其他州省」的最小像素距离，并记录该州
  规则：gap_other < gap_own → 并入该州（地理上更贴近别国）；否则保留（只是隔了小海峡）
用法：python fix_enclaves3.py [--dry] [--same-owner]
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
ONLY_SAME = '--same-owner' in sys.argv
MAXGAP = 40

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

# 连通分量（2px 桥接）
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


def gaps(blk, own_states, other_map):
    """块到本州其他省 / 其他州省的最小像素距离"""
    ys, xs = np.nonzero(np.isin(prov, blk))
    y0, y1 = max(0, ys.min() - MAXGAP), min(H, ys.max() + MAXGAP + 1)
    x0, x1 = max(0, xs.min() - MAXGAP), min(W, xs.max() + MAXGAP + 1)
    sub = prov[y0:y1, x0:x1]
    inblk = np.isin(sub, blk)
    pts = np.argwhere(inblk)                 # (y,x) 在 sub 内
    best_own, best_other, other_p = 10 ** 9, 10 ** 9, None
    # 逐省算（只算 sub 内出现的省，且排除本块）
    cand = [p for p in np.unique(sub).tolist()
            if p and p not in set(blk) and p in p2s and p in LAND]
    for q in cand:
        qm = (sub == q)
        qp = np.argwhere(qm)
        if len(qp) == 0:
            continue
        d = np.sqrt(((qp[:, None, :] - pts[None, :, :]) ** 2).sum(-1)).min()
        if p2s[q] in own_states:
            best_own = min(best_own, d)
        else:
            if d < best_other:
                best_other, other_p = d, q
    return best_own, best_other, other_p


plan, keep = [], []
for sid, ps in sorted(s2p.items()):
    lps = [p for p in ps if p in LAND]
    if len(lps) < 2:
        continue
    c = comps(lps, adj2)
    if len(c) == 1:
        continue
    main = c[0]
    for blk in c[1:]:
        # 只关心"没有主体相邻"的块（2px 内接不到主体）
        go, goth, op = gaps(blk, {sid}, p2s)
        if go <= 2:
            continue                        # 与主体相接（细缝），不算飞地
        if goth < go and op is not None:
            tgt = p2s[op]
            if ONLY_SAME and s2o.get(tgt) != s2o.get(sid):
                keep.append((sid, blk, go, goth, tgt, '跨国，跳过'))
                continue
            plan.append((sid, s2o.get(sid), blk, go, goth, tgt, s2o.get(tgt)))
        else:
            keep.append((sid, blk, go, goth, None, '本体更近（仅隔海峡）'))

print(f'=== 拟修：{len(plan)} 处 ===')
for sid, tag, blk, go, goth, tgt, ttag in plan:
    print(f'  state {sid}({tag}) 省 {blk}: 距本州 {go:.0f}px、距 state {tgt}({ttag}) {goth:.0f}px'
          + ('   ⚠ 国家变更' if tag != ttag else ''))
print(f'\n=== 保留（本体更近/跳过）：{len(keep)} 处 ===')
for sid, blk, go, goth, tgt, why in keep:
    print(f'  state {sid} 省 {blk}: 距本州 {go:.0f}px、距他州 {goth:.0f}px → {why}')

if DRY or not plan:
    print('\n[DRY / 未写盘]')
    sys.exit(0)

bdir = os.path.join(ROOT, '.backups', 'enclave3_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
touched = set()
for sid, tag, blk, go, goth, tgt, ttag in plan:
    for p in blk:
        if p in s2p[sid]:
            s2p[sid].remove(p)
        if p not in s2p[tgt]:
            s2p[tgt].append(p)
    touched.add(sid)
    touched.add(tgt)
PB = re.compile(r'\t\t\t(\d+) = \{\r\n(?:\t\t\t\t[^\r\n]*\r\n)+\t\t\t\}')
work = {s: raw[s] for s in touched}
for sid, tag, blk, go, goth, tgt, ttag in plan:
    for p in blk:
        for m in PB.finditer(work[sid]):
            if int(m.group(1)) == p:
                work[tgt] = re.sub(r'(\t\tbuildings = \{)',
                                   lambda mm: mm.group(1) + '\r\n' + m.group(0), work[tgt], count=1)
                work[sid] = work[sid].replace(m.group(0) + '\r\n', '')
                print(f'  省 {p}: 携带省级建筑块 → state {tgt}')
                break
for sid in sorted(touched):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = re.sub(r'(provinces = \{\r\n\t\t)[^\r\n]*(\r\n\t\})',
               lambda m: f'{m.group(1)}{" ".join(map(str, sorted(s2p[sid])))}{m.group(2)}', work[sid])
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)
print(f'\n已写入 {len(touched)} 个州文件，备份 {bdir}')

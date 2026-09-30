# -*- coding: utf-8 -*-
"""
多州省均分（紧凑优化版）：python rebalance_states.py 584,595,607,618 [--dry]

· 州号列表来自命令行（逗号/全角逗号分隔）
· 16 次随机化重试，选「紧凑度」最优的分法：
    组评分 = 组内省质心最大距离 / 等面积圆直径（圆=1，越大越条状）
    总评 = 按省数加权平均；另惩罚省数失衡
· province 数（含省级建筑块/胜利点）跟随，语法自检
"""
import os, re, sys, math, heapq, itertools, shutil, datetime, random, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

argv = [a for a in sys.argv[1:] if not a.startswith('--')]
DRY = '--dry' in sys.argv
STATES = []
for a in argv:
    for x in re.split(r'[,\uff0c]+', a):
        x = x.strip()
        if x.isdigit():
            STATES.append(int(x))
STATES = sorted(set(STATES))
assert len(STATES) >= 2, '至少两个州'
print(f'均分州：{STATES}')

# ---- 几何 ----
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
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)
land_ids = {p for p, k in kind.items() if k == 'land' and p <= int(prov.max())}

BRIDGE = 2
src = np.where(np.isin(prov, list(land_ids)), prov, 0)
adj = collections.defaultdict(set)
for r in range(0, BRIDGE + 1):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if r == 0 and not (dx or dy):
                continue
            a = src[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)]
            b = src[max(0, dy):H - max(0, -dy), max(0, dx):W - max(0, -dx)]
            m = (a != b) & (a > 0) & (b > 0)
            for x, y in zip(a[m].tolist(), b[m].tolist()):
                adj[x].add(y)
                adj[y].add(x)

flat = prov.ravel()
gx = np.tile(np.arange(W, dtype=np.float64), H)
gy = np.repeat(np.arange(H, dtype=np.float64), W)
npx = np.bincount(flat, minlength=int(prov.max()) + 2)
cx = np.bincount(flat, weights=gx, minlength=len(npx)) / np.maximum(npx, 1)
cy = np.bincount(flat, weights=gy, minlength=len(npx)) / np.maximum(npx, 1)

s2p, s2o, raw = {}, {}, {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2o[sid] = re.search(r'\bowner\s*=\s*(\w+)', t).group(1)
    s2p[sid] = [int(x) for x in re.search(r'provinces = \{([^}]*)\}', t).group(1).split()]
    raw[sid] = t
for s in STATES:
    print(f'  state {s}({s2o[s]}): {len(s2p[s])} 省')

P = [p for s in STATES for p in s2p[s] if p in land_ids]
K = len(STATES)
print(f'并集 {len(P)} 省 → {K} 份（目标 ~{len(P)/K:.1f} 省/州）')

ps, seen, blocks = set(P), set(), []
for p in ps:
    if p in seen:
        continue
    blk, q = [], [p]
    seen.add(p)
    while q:
        u = q.pop()
        blk.append(u)
        for v in adj[u]:
            if v in ps and v not in seen:
                seen.add(v)
                q.append(v)
    blocks.append(sorted(blk))
blocks.sort(key=len, reverse=True)
print(f'连通块: {[len(b) for b in blocks]}')


def dmax_group(g):
    """组内省质心最大距离"""
    pts = np.array([[cx[p], cy[p]] for p in g])
    if len(pts) < 2:
        return 0.0
    return float(np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1)).max())


def score(groups):
    """总评：紧凑度（加权平均，越小越紧凑）+ 规模失衡惩罚"""
    tot_px = sum(npx[p] for g in groups for p in g)
    sc, wsum = 0.0, 0
    worst = 0.0
    for g in groups:
        a = sum(npx[p] for p in g)
        if a <= 0 or len(g) < 2:
            return 1e9
        d = dmax_group(g)
        circle_d = 2 * math.sqrt(a / math.pi)
        s = d / max(circle_d, 1)
        sc += s * a
        wsum += a
        worst = max(worst, s)
    imb = max(len(g) for g in groups) - min(len(g) for g in groups)
    return sc / wsum + worst * 0.3 + imb * 0.08


def grow(seeds, P, cap):
    own, sizes = {}, [0] * len(seeds)
    heap, tie, sp = [], itertools.count(), set()
    for i, sd in enumerate(seeds):
        own[sd] = i
        sizes[i] = 1
        sp.add(sd)
        for v in adj[sd]:
            if v in P and (v, i) not in sp:
                sp.add((v, i))
                heapq.heappush(heap, (1, next(tie), v, i))
    while heap:
        _, _, p, r = heapq.heappop(heap)
        if p in own or sizes[r] >= cap:
            continue
        own[p] = r
        sizes[r] += 1
        for v in adj[p]:
            if v in P and v not in own and (v, r) not in sp:
                sp.add((v, r))
                heapq.heappush(heap, (sizes[r], next(tie), v, r))
    return own


def partition(pset, k, maxsz, minsz, rng):
    pset = list(pset)
    P = set(pset)
    # 种子：最远点采样，但每次从前 4 远随机挑一个（随机化）
    seeds = [rng.choice(pset)]
    for _ in range(k - 1):
        cands = sorted(((min((cx[p] - cx[q]) ** 2 + (cy[p] - cy[q]) ** 2 for q in seeds), p)
                        for p in pset if p not in seeds), reverse=True)[:4]
        seeds.append(rng.choice(cands)[1])
    k = len(seeds)
    cap = max(minsz, min(maxsz, math.ceil(len(pset) / k) + (1 if len(pset) % k else 0)))
    own = grow(seeds, P, cap)
    left = [p for p in pset if p not in own]
    for _ in range(50):
        if not left:
            break
        nxt = []
        for p in left:
            nb = [own[v] for v in adj[p] if v in own]
            if nb:
                own[p] = collections.Counter(nb).most_common(1)[0][0]
            else:
                nxt.append(p)
        left = nxt
    for p in left:
        own[p] = 0
    grp = collections.defaultdict(list)
    for p, r in own.items():
        grp[r].append(p)
    groups = [sorted(v) for v in grp.values()]
    guard = 0
    while guard < 300 and len(groups) < k:
        guard += 1
        groups.sort(key=len, reverse=True)
        g = groups[0]
        if len(g) < 2 * minsz:
            break
        sub = partition(g, 2, maxsz, minsz, rng)
        if len(sub) > 1:
            groups = groups[1:] + sub
    return groups


def comps(pset):
    ps, seen, k = set(pset), set(), 0
    for p in ps:
        if p in seen:
            continue
        k += 1
        q = [p]
        seen.add(p)
        while q:
            u = q.pop()
            for v in adj[u]:
                if v in ps and v not in seen:
                    seen.add(v)
                    q.append(v)
    return k


def split_all(rng):
    ks = [1] * len(blocks)
    rem = K - len(blocks)
    sizes = [len(b) for b in blocks]
    guard = 0
    while rem > 0 and guard < 100:
        guard += 1
        cand = [i for i in range(len(blocks)) if ks[i] < max(1, sizes[i] // 3)] or list(range(len(blocks)))
        i = max(cand, key=lambda i: sizes[i] / ks[i])
        ks[i] += 1
        rem -= 1
    if rem > 0:
        return None
    groups = []
    for i, blk in enumerate(blocks):
        if ks[i] == 1:
            groups.append(list(blk))
        else:
            groups.extend(partition(blk, ks[i], maxsz=math.ceil(max(sizes) / max(K, 1)) + 1,
                                    minsz=2, rng=rng))
    if len(groups) != K:
        return None
    if any(comps(g) > 1 for g in groups):
        return None
    return groups


best, best_s, best_rng = None, 1e9, None
for it in range(16):
    rng = random.Random(it)
    groups = split_all(rng)
    if groups is None:
        continue
    s = score(groups)
    if s < best_s:
        best, best_s, best_rng = groups, s, it
if best is None:
    print('!! 16 次重试都没得到合法分组，中止')
    sys.exit(1)
print(f'最优第 {best_rng} 次重试，总评 {best_s:.3f}')
for g in best:
    d = dmax_group(g)
    a = sum(npx[p] for p in g)
    print(f'  组 {len(g)} 省  紧凑度 {d / max(2 * math.sqrt(a / math.pi), 1):.2f}  {g}')

# 组 → 州：按省重叠最多
avail = set(STATES)
assign = {}
for g in sorted(best, key=len, reverse=True):
    b, bo = None, -1
    for s in avail:
        o = len(set(g) & set(s2p[s]))
        if o > bo:
            b, bo = s, o
    assign[b] = g
    avail.discard(b)
for s in STATES:
    print(f'  state {s}({s2o[s]}) -> {len(assign[s])} 省')

# 收集省级建筑块/胜利点
PB = re.compile(r'\t\t\t(\d+) = \{\r\n(?:\t\t\t\t[^\r\n]*\r\n)+\t\t\t\}')
prov_block, prov_vp = {}, {}
for s, t in raw.items():
    bm = re.search(r'\t\tbuildings = \{', t)
    if bm:
        depth, i, end = 0, bm.end() - 1, None
        while i < len(t):
            if t[i] == '{':
                depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
            i += 1
        body = t[bm.end() - 1:end + 1]
        for m in PB.finditer(body):
            prov_block[int(m.group(1))] = m.group(0)
    for m in re.finditer(r'victory_points = \{([^}]*)\}', t):
        v = m.group(1).split()
        for i2 in range(0, len(v) - 1, 2):
            prov_vp[int(v[i2])] = int(v[i2 + 1])


def rebuild_state(sid, newps, t):
    t = re.sub(r'(provinces = \{\r\n\t\t)[^\r\n]*(\r\n\t\})',
               lambda m: f'{m.group(1)}{" ".join(map(str, sorted(newps)))}{m.group(2)}', t)
    bm = re.search(r'\t\tbuildings = \{', t)
    if bm:
        depth, i, end = 0, bm.end() - 1, None
        while i < len(t):
            if t[i] == '{':
                depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
            i += 1
        body = t[bm.end() - 1:end + 1]
        bl = body.split('\r\n')
        keep, j = [], 1
        while j < len(bl) - 1:
            ln = bl[j]
            if re.match(r'\t\t\t\d+ = \{', ln):
                k2 = j + 1
                while k2 < len(bl) - 1 and bl[k2] != '\t\t\t}':
                    k2 += 1
                j = k2 + 1
                continue
            if re.match(r'\t\t\t[a-z_]\w* = .+', ln):
                keep.append(ln)
            j += 1
        blocks = [prov_block[p] for p in sorted(newps) if p in prov_block]
        newbody = '\t\tbuildings = {\r\n' + '\r\n'.join(keep + blocks) + '\r\n\t\t}'
        t = t[:bm.start()] + newbody + t[end + 1:]
    vps = [(p, prov_vp[p]) for p in sorted(newps) if p in prov_vp]
    line = ('victory_points = { ' + ' '.join(f'{p} {v}' for p, v in vps) + ' }') if vps else None
    if re.search(r'victory_points = \{[^}]*\}', t):
        if line:
            t = re.sub(r'victory_points = \{[^}]*\}', line, t)
        else:
            t = re.sub(r'\r\n\t\tvictory_points = \{[^}]*\}', '', t)
    elif line:
        hm = re.search(r'\thistory = \{', t)
        depth, i, end = 0, hm.end() - 1, None
        while i < len(t):
            if t[i] == '{':
                depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
            i += 1
        ls = t.rfind('\r\n', 0, end) + 2
        t = t[:ls] + '\t\t' + line + '\r\n' + t[ls:]
    return t


if DRY:
    print('\n[DRY] 未写盘')
    sys.exit(0)

bdir = os.path.join(ROOT, '.backups', 'state_rebalance_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
for s in STATES:
    fp = os.path.join(ST, f'{s}-State_{s}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(rebuild_state(s, assign[s], raw[s]))
print(f'已写入 {len(STATES)} 个州文件，备份 {bdir}')

syn = collections.Counter()
all_own = collections.defaultdict(list)
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    if t.count('{') != t.count('}'):
        syn['括号'] += 1
    pl = re.search(r'provinces = \{\r\n\t\t([^\r\n]*)\r\n\t\}', t).group(1).split()
    if not pl:
        syn['空州'] += 1
    for p in pl:
        all_own.setdefault(p, []).append(f)
    for m in re.finditer(r'victory_points = \{([^}]*)\}', t):
        for pid in m.group(1).split()[0::2]:
            if pid not in pl:
                syn['胜利点越州'] += 1
dup = {p: v for p, v in all_own.items() if len(v) > 1}
print(f'语法自检: {dict(syn) if syn else "0 问题 ✓"}；重复归属 {len(dup)}')

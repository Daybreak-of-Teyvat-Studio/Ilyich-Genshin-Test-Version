# -*- coding: utf-8 -*-
"""
整合各国 state：每州必须连通，陆地 3~8 省（岛屿允许 1~2）。

  阶段A  你点名的两处飞地归位：928 -> state 464，464 -> state 222
  阶段B  其余"孤悬别国腹地"的飞地 → 并入包围它的那个州（跨国）
         判定：与该州主体像素距离 > FAR 才算真飞地；<= BRIDGE 的当作连通（栅格化缝隙）
  阶段C  按国家重排（保持州数不变）：连通 + 均衡 3~8；蒙德系/璃月系/天理 不动

  州级数值（manpower/resources/state_category）保持在各州文件里不动；
  省级建筑块与胜利点跟着省走。

  python integrate_states.py [--dry]
"""
import os, re, sys, math, heapq, collections, shutil, datetime
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
sys.path.insert(0, ROOT)
from gamma_regions import tag_cn
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')
DRY = '--dry' in sys.argv
FAR = 15          # 超过这个像素距离才算"真飞地"
BRIDGE = 2        # 这个距离内视为连通（跳过栅格化缝隙）

# ---------------- 几何 ----------------
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
    klut[i] = 1 if kind.get(pid, 'land') == 'land' else 0
prov = plut[inv].reshape(H, W)
land = klut[inv].reshape(H, W).astype(bool)

# 省质心 + bbox
flat = prov.ravel()
gx = np.tile(np.arange(W, dtype=np.float64), H)
gy = np.repeat(np.arange(H, dtype=np.float64), W)
N = int(prov.max()) + 2
npx = np.bincount(flat, minlength=N)
cx = np.bincount(flat, weights=gx, minlength=N) / np.maximum(npx, 1)
cy = np.bincount(flat, weights=gy, minlength=N) / np.maximum(npx, 1)
land_ids = {p for p, k in kind.items() if k == 'land' and npx[p] > 0}
print(f'省 {len(land_ids)} / 地图 {W}x{H}')

# 邻接：4 邻域 + 膨胀 BRIDGE 像素（跨过栅格化细缝）
adj = collections.defaultdict(set)
src = np.where(land & (prov > 0), prov, 0)
for r in range(0, BRIDGE + 1):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if r == 0 and not (dx or dy):
                continue
            a = src[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)]
            b = src[max(0, dy):H - max(0, -dy), max(0, dx):W - max(0, -dx)]
            m = (a != b) & (a > 0) & (b > 0)
            for x, y in zip(a[m].tolist(), b[m].tolist()):
                if x != y:
                    adj[x].add(y)
                    adj[y].add(x)
print(f'邻接边 {sum(len(v) for v in adj.values()) // 2}')

# ---------------- 州 ----------------
s2p, s2o, raw = {}, {}, {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2o[sid] = re.search(r'\bowner\s*=\s*(\w+)', t).group(1)
    s2p[sid] = [int(x) for x in re.search(r'provinces = \{([^}]*)\}', t).group(1).split()]
    raw[sid] = t
p2s = {p: s for s, ps in s2p.items() for p in ps}


def comps(pset, use_adj=None):
    A = use_adj if use_adj is not None else adj
    ps = set(pset)
    seen, out = set(), []
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
        out.append(blk)
    return sorted(out, key=len, reverse=True)


def pxdist(pa, pb):
    """两个省集合的最近像素距离（抽样：用两省的像素点集，量大时用边界近似）"""
    ya, xa = np.nonzero(prov == pa if isinstance(pa, int) else np.isin(prov, list(pa)))
    yb, xb = np.nonzero(prov == pb if isinstance(pb, int) else np.isin(prov, list(pb)))
    if not len(ya) or not len(yb):
        return 1e9
    A = np.stack([xa, ya], 1).astype(np.float64)
    B = np.stack([xb, yb], 1).astype(np.float64)
    if len(A) * len(B) > 4_000_000:      # 抽样，够用
        A = A[::max(1, len(A) // 2000)]
        B = B[::max(1, len(B) // 2000)]
    d = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1))
    return float(d.min())


# ---------------- 阶段A：点名飞地归位 ----------------
moves = collections.defaultdict(list)
touched = set()                     # 阶段A/B 改动过的州（含受保护国家，也必须写盘）
for p, dst in ((928, 464), (464, 222)):
    src_ = p2s[p]
    if src_ == dst:
        continue
    moves[src_].append(p)
    moves[dst].append(p)
    p2s[p] = dst
    print(f'阶段A: 省 {p}  state {src_} -> {dst}（{s2o[dst]}）')
for s, ps in list(moves.items()):
    pass
for s in set(list(moves)):
    s2p[s] = [p for p in s2p[s] if p2s[p] == s] + [p for p in moves[s] if p2s[p] == s and p not in s2p[s]]
    s2p[s] = sorted(set(s2p[s]))
    touched.add(s)

# ---------------- 阶段B：其余真飞地交给包围它的州 ----------------
MOT = {'MOT', 'DVA', 'RAG', 'LAW', 'GUN', 'FAV', 'SPI', 'ANR', 'DRA'}
LYY = {'LYY', 'BRF', 'KQP', 'SHP', 'GYP', 'CYG', 'YLH'}
PROTECT = MOT | LYY | {'PRI'}          # 不主动从这些国家身上割地（但可以接收）

handover = []
for it in range(4):
    changed = 0
    for s in sorted(s2p):
        ps = [p for p in s2p[s] if p in land_ids]
        if len(ps) < 2:
            continue
        cs = comps(ps)
        if len(cs) == 1:
            continue
        main = cs[0]
        for c in cs[1:]:
            if pxdist(main, c) <= FAR:        # 近邻：算连通，不动
                continue
            # 找与这块共享边界最多的邻州
            cnt = collections.Counter()
            for p in c:
                for q in adj[p]:
                    qs = p2s.get(q)
                    if qs is not None and qs != s:
                        cnt[qs] += 1
            if not cnt:
                continue                       # 孤立海岛：留作自己的州
            tgt = cnt.most_common(1)[0][0]
            handover.append((s, tgt, list(c), cnt[tgt]))
            for p in c:
                p2s[p] = tgt
            s2p[s] = [p for p in s2p[s] if p2s[p] == s]
            s2p[tgt] = sorted(set(s2p[tgt] + list(c)))
            changed += 1
    if not changed:
        break
print(f'\n阶段B: 真飞地归位 {len(handover)} 处')
for a, b, c, k in handover:
    print(f'   state {a}({s2o[a]}) -> state {b}({s2o[b]})  {len(c)} 省 {sorted(c)[:8]}  共享边界 {k}')

# ---------------- 阶段C：按国家重排 ----------------
def partition(pset, k, maxsz=8, minsz=3, depth=0):
    """把连通的省集合分成 k 个连通组，尽量均衡"""
    pset = list(pset)
    if k <= 1:
        return [pset]
    P = set(pset)
    # 最远点采样选种子
    seeds = [pset[0]]
    for _ in range(k - 1):
        best, bd = None, -1
        for p in pset:
            if p in seeds:
                continue
            d = min((cx[p] - cx[q]) ** 2 + (cy[p] - cy[q]) ** 2 for q in seeds)
            if d > bd:
                best, bd = p, d
        if best is None:
            break
        seeds.append(best)
    k = len(seeds)
    cap = max(minsz, min(maxsz, math.ceil(len(pset) / k)))
    own, sizes = {}, [0] * k
    heap = []
    import itertools
    tie = itertools.count()
    seen_pair = set()
    for i, sd in enumerate(seeds):
        own[sd] = i
        sizes[i] = 1
        for v in adj[sd]:
            if v in P and (v, i) not in seen_pair:
                seen_pair.add((v, i))
                heapq.heappush(heap, (1, next(tie), v, i))
    # 谁小谁先长；区域满了就不认领，由别的区域接手（所以省可能被多次入队，这是对的）
    while heap:
        _, _, p, r = heapq.heappop(heap)
        if p in own or sizes[r] >= cap:
            continue
        own[p] = r
        sizes[r] += 1
        for v in adj[p]:
            if v in P and v not in own and (v, r) not in seen_pair:
                seen_pair.add((v, r))
                heapq.heappush(heap, (sizes[r], next(tie), v, r))
    # 兜底：漏掉的挂到最近的已分配邻省（沿邻接多轮扩散）
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
    # 修复
    for _ in range(200):
        grp = collections.defaultdict(set)
        for p, r in own.items():
            grp[r].add(p)
        small = [r for r, g in grp.items() if len(g) < minsz]
        big = [r for r, g in grp.items() if len(g) > maxsz]
        if not small and not big:
            break
        if small:
            r = small[0]
            nb = collections.Counter(own[v] for p in grp[r] for v in adj[p]
                                     if v in own and own[v] != r)
            if not nb:
                break
            t = nb.most_common(1)[0][0]
            for p in grp[r]:
                own[p] = t
            continue
        r = big[0]
        done = False
        for p in sorted(grp[r], key=lambda x: -min((cx[x] - cx[q]) ** 2 + (cy[x] - cy[q]) ** 2
                                                   for q in grp[r] if q != x)):
            rest = grp[r] - {p}
            if len(comps(rest)) > 1:
                continue
            nb = collections.Counter(own[v] for v in adj[p] if v in own and own[v] != r)
            for t, _ in nb.most_common():
                if len(grp.get(t, ())) < maxsz:
                    own[p] = t
                    done = True
                    break
            if done:
                break
        if not done:
            break
    out = collections.defaultdict(list)
    for p, r in own.items():
        out[r].append(p)
    groups = [sorted(v) for v in out.values()]
    # 修补：① 任何 >maxsz 的组按 ceil(size/maxsz) 拆开 ② 组数不足 k 时继续二分
    guard = 0
    while guard < 400 and depth < 12:
        guard += 1
        changed = False
        for g in sorted(groups, key=len, reverse=True)[:8]:
            if len(g) > maxsz:
                m = max(2, math.ceil(len(g) / maxsz))
                sub = partition(g, m, maxsz, minsz, depth + 1)
                if len(sub) > 1:
                    groups = [x for x in groups if x is not g] + sub
                    changed = True
                    break
        if changed:
            continue
        if len(groups) < k:
            groups.sort(key=len, reverse=True)
            g = groups[0]
            if len(g) >= 2 * minsz:
                sub = partition(g, 2, maxsz, minsz, depth + 1)
                if len(sub) > 1:
                    groups = groups[1:] + sub
                    changed = True
        if not changed:
            break
    return groups


TARGET = [c for c in sorted(set(s2o.values())) if c not in PROTECT]
print(f'\n阶段C: 参与重排的国家 {len(TARGET)} 个')
assign = {}          # state -> new province list
for c in TARGET:
    sts = [s for s in s2p if s2o[s] == c]
    P_all = [p for s in sts for p in s2p[s]]
    P = [p for p in P_all if p in land_ids]
    drop = [p for p in P_all if p not in land_ids]      # definition 里有、位图里无像素的省
    if not P:
        continue
    cs = comps(P)
    ktot = len(sts)
    sizes = [len(x) for x in cs]
    # 州数按连通块大小分配：每块至少 1，且每块 ks <= max(1, size//3)（保证每州 >=3 省）
    ks = [1] * len(cs)
    rem = ktot - len(cs)
    while rem > 0:
        cand = [i for i in range(len(cs)) if ks[i] < max(1, sizes[i] // 3)]
        if not cand:
            break
        i = max(cand, key=lambda i: sizes[i] / ks[i])
        ks[i] += 1
        rem -= 1
    if rem:
        print(f'   ! {c}: 还有 {rem} 个州没分到连通块（州数多于几何允许）')
    groups = []
    for i, blk in enumerate(cs):
        for g in partition(blk, ks[i]):
            groups.append(g)
    if len(groups) < ktot:
        print(f'   ! {c}: 只生成 {len(groups)} 组 < 州数 {ktot}')
    # 组 -> 州文件：按重叠最多分配
    avail = set(sts)
    asg = {}
    for g in sorted(groups, key=len, reverse=True):
        best, bo = None, -1
        for s in avail:
            o = len(set(g) & set(s2p[s]))
            if o > bo:
                best, bo = s, o
        if best is None:                     # 州文件不够用（不该发生）
            continue
        asg[best] = g
        avail.discard(best)
    for s in avail:                          # 没用上的州：留给下面的补齐逻辑
        pass
    # 无像素省：挂到同国最近的已分配州（保证不丢省）
    for p in drop:
        if not asg:
            break
        def _d(s):
            g = asg[s]
            return (cx[p] - sum(cx[q] for q in g) / len(g)) ** 2 + \
                   (cy[p] - sum(cy[q] for q in g) / len(g)) ** 2
        t0 = min(asg, key=_d)
        asg[t0] = sorted(set(asg[t0]) | {p})
        touched.add(t0)
    for s, g in asg.items():
        assign[s] = g
print(f'已生成 {len(assign)} 个州的新省列表')

# leftover 州（组数少于州数时出现）：从同国最大的组里拆一块给它，避免出现空州
leftover = [s for s in s2p if s not in assign and s2o[s] in TARGET]
if leftover:
    print(f'空州 {len(leftover)} 个，需从同国大组里拆补: {leftover[:12]}')
    for s in leftover:
        cands = sorted([(len(g), t) for t, g in assign.items()
                        if s2o.get(t) == s2o[s] and len(g) >= 2], reverse=True)
        done = False
        for n, t in cands:
            if n < 2:
                break
            sub = partition(assign[t], 2, 8, 1)
            if len(sub) == 2:
                sub.sort(key=len)
                assign[t] = sub[1]
                assign[s] = sub[0]
                done = True
                break
        if not done:
            print(f'   ! state {s}({s2o[s]}) 无法拆补，保持原省列表')
            assign[s] = s2p[s]

# ---------------- 校验 ----------------
bad_c = bad_s = 0
land_groups = collections.Counter()
for s, g in assign.items():
    if not g:
        continue
    k = len(comps(g))
    if k > 1:
        bad_c += 1
        if bad_c <= 10:
            print(f'   ! state {s} 仍不连通（{len(g)}省/{k}块）')
    gl = [p for p in g if p in land_ids]
    if gl:
        land_groups[len(gl)] += 1
        if len(gl) > 8 or len(gl) < 3:
            bad_s += 1
print(f'\n校验: 不连通州 {bad_c}；省数不在 3~8 的州 {bad_s}')
print(f'省数分布: {dict(sorted(land_groups.items()))}')

if DRY:
    print('\n[DRY] 未写盘')
    sys.exit(0)

# ---------------- 写盘 ----------------
# 1) 全局收集：每个省的省级建筑块 与 胜利点（从任意州文件里）
import shutil, datetime
PB = re.compile(r'\t\t\t(\d+) = \{\r\n((?:\t\t\t\t[^\r\n]*(?:\r\n))+)+\t\t\t\}')
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
print(f'\n收集到省级建筑块 {len(prov_block)} 个、胜利点 {len(prov_vp)} 个')


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
        # 按花括号配对剥离省级子块：只保留「州级 key = value」行，丢掉省块及其内部行
        bl = body.split('\r\n')
        keep, i2 = [], 1
        while i2 < len(bl) - 1:
            ln = bl[i2]
            if re.match(r'\t\t\t\d+ = \{', ln):
                j = i2 + 1
                while j < len(bl) - 1 and bl[j] != '\t\t\t}':
                    j += 1
                i2 = j + 1
                continue
            if re.match(r'\t\t\t[a-z_]\w* = .+', ln):
                keep.append(ln)
            i2 += 1
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


bdir = os.path.join(ROOT, '.backups',
                    'state_integrate_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
n = 0
write_set = set(assign) | touched
for s in sorted(write_set):
    g = assign.get(s, s2p[s])
    if not g:
        continue
    orig = [int(x) for x in re.search(r'provinces = \{([^}]*)\}', raw[s]).group(1).split()]
    if sorted(g) == sorted(orig):
        continue
    shutil.copy2(os.path.join(ST, f'{s}-State_{s}.txt'), os.path.join(bdir, f'{s}-State_{s}.txt'))
    t = rebuild_state(s, g, raw[s])
    with open(os.path.join(ST, f'{s}-State_{s}.txt'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)
    n += 1
print(f'已写入 {n} 个州文件，备份 {bdir}')

# 1.2) 语法自检（上轮就是漏了这道关卡才崩的）
syn = collections.Counter()
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    if t.count('{') != t.count('}'):
        syn['总花括号不配对'] += 1
    if re.search(r'(?m)^ +', t):
        syn['行首空格'] += 1
    bm = re.search(r'\t\tbuildings = \{', t)
    if bm:
        depth, i3, end3 = 0, bm.end() - 1, None
        while i3 < len(t):
            if t[i3] == '{':
                depth += 1
            elif t[i3] == '}':
                depth -= 1
                if depth == 0:
                    end3 = i3
                    break
            i3 += 1
        if end3 is None:
            syn['buildings 块未闭合'] += 1
        else:
            body = t[bm.end() - 1:end3 + 1]
            bl = body.split('\r\n')
            i4, ok_blk = 1, True
            while i4 < len(bl) - 1:
                ln = bl[i4]
                if re.match(r'\t\t\t\d+ = \{', ln):
                    j = i4 + 1
                    while j < len(bl) - 1 and bl[j] != '\t\t\t}':
                        if not re.match(r'\t\t\t\t', bl[j]):
                            ok_blk = False
                        j += 1
                    if j >= len(bl) - 1:
                        ok_blk = False
                    i4 = j + 1
                    continue
                if not re.match(r'\t\t\t[a-z_]\w* = .+', ln):
                    ok_blk = False          # 孤立的 4-tab 行 / 多余 }
                i4 += 1
            if not ok_blk:
                syn['buildings 块结构错'] += 1
    pl = set(re.search(r'provinces = \{\r\n\t\t([^\r\n]*)\r\n\t\}', t).group(1).split())
    if not pl:
        syn['provinces 为空'] += 1
    for m in re.finditer(r'victory_points = \{([^}]*)\}', t):
        v = m.group(1).split()
        if len(v) % 2:
            syn['victory_points 字段数奇数'] += 1
        for pid in v[0::2]:
            if pid not in pl:
                syn['胜利点省不在本州'] += 1
    if len(re.findall(r'victory_points = \{', t)) > 1:
        syn['victory_points 重复'] += 1
    o = re.findall(r'(?m)^\t\towner = (\w+)\r?$', t)
    c2 = re.findall(r'(?m)^\t\tadd_core_of = (\w+)\r?$', t)
    if len(o) != 1 or c2 != o:
        syn['owner/核心异常'] += 1
print(f'语法自检: {dict(syn) if syn else "0 问题 ✓"}')

# 1.5) 兜底网：任何陆地省若在磁盘上不属于任何州，挂到同国最近的州
import subprocess
on_disk = {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for p in re.findall(r'\d+', re.search(r'provinces = \{([^}]*)\}', t).group(1)):
        on_disk[int(p)] = sid
lost = sorted(p for p in land_ids if p not in on_disk)
if lost:
    print(f'兜底: 发现 {len(lost)} 个无归属省 {lost}')
    for p in lost:
        cand = [(np.hypot(cx[p] - sum(cx[q] for q in s2p[s]) / max(1, len(s2p[s])),
                          cy[p] - sum(cy[q] for q in s2p[s]) / max(1, len(s2p[s]))), s)
                for s in s2p if s2o[s] == s2o.get(p2s.get(p, 0), '')]
        if not cand:
            cand = [(0.0, p2s.get(p, next(iter(s2p))))]
        s = min(cand)[1]
        t = open(os.path.join(ST, f'{s}-State_{s}.txt'), encoding='utf-8-sig', newline='').read()
        pl = sorted(set(int(x) for x in re.search(r'provinces = \{([^}]*)\}', t).group(1).split()) | {p})
        t = re.sub(r'(provinces = \{\r\n\t\t)[^\r\n]*(\r\n\t\})',
                   lambda m: f'{m.group(1)}{" ".join(map(str, pl))}{m.group(2)}', t)
        with open(os.path.join(ST, f'{s}-State_{s}.txt'), 'w', encoding='utf-8', newline='') as fh:
            fh.write(t)
        print(f'   省 {p} -> state {s}（{s2o[s]}）')
        on_disk[p] = s
    print(f'兜底后: 州文件里的省 {len(on_disk)} / definition 陆地省 {len(land_ids)}')

# 2) 同步 map/buildings.txt（省->州 全变了）
import subprocess
r = subprocess.run([sys.executable, os.path.join(ROOT, 'rebuild_buildings.py')],
                   cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
print(r.stdout[-1200:] if r.returncode == 0 else f'!! buildings 重建失败\n{r.stdout}\n{r.stderr}')


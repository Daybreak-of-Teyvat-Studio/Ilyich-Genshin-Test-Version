# -*- coding: utf-8 -*-
"""
海洋划分：以省 4928、6201 质心为对角线的矩形内海省 → 均分 40 个新州（862-901）；
区域外海省 → 新州 902「暗之外海」。新州无 owner（纯海域），落地 definition 不动、
terrain.bmp 不动，之后跑 rebuild_buildings.py 同步海面建筑条目。
"""
import os, re, sys, math, heapq, itertools, collections, datetime
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
K_IN = 40

# 省几何
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
flat = prov.ravel()
npx = np.bincount(flat, minlength=int(prov.max()) + 2)
gx = np.tile(np.arange(W, dtype=np.float64), H)
gy = np.repeat(np.arange(H, dtype=np.float64), W)
cx = np.bincount(flat, weights=gx, minlength=len(npx)) / np.maximum(npx, 1)
cy = np.bincount(flat, weights=gy, minlength=len(npx)) / np.maximum(npx, 1)

# 州省（陆）
s2p, s2o, raw = {}, {}, {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2o[sid] = re.search(r'\bowner\s*=\s*(\w+)', t).group(1)
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
    raw[sid] = t
p2s = {p: s for s, ps in s2p.items() for p in ps}

# 海省 = definition 非 land 且不属于任何州
kind = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
sea = sorted(p for p, k in kind.items() if k != 'land' and p not in p2s and npx[p] > 0)
print(f'海省 {len(sea)} 个（无归属）')

p1, p2 = 4928, 6201
x1, x2 = sorted((cx[p1], cx[p2]))
y1, y2 = sorted((cy[p1], cy[p2]))
print(f'对角线: x[{x1:.0f},{x2:.0f}] y[{y1:.0f},{y2:.0f}]')
inside = [p for p in sea if x1 <= cx[p] <= x2 and y1 <= cy[p] <= y2]
outside = [p for p in sea if p not in set(inside)]
print(f'区域内 {len(inside)} 省 / 区域外 {len(outside)} 省')

# 海省邻接（4 邻域）
seaset = set(sea)
adj = collections.defaultdict(set)
src = np.where(np.isin(prov, sea), prov, 0)
for a_, b_ in ((src[:, :-1], src[:, 1:]), (src[:-1, :], src[1:, :])):
    m = (a_ != b_) & (a_ > 0) & (b_ > 0)
    for x, y in zip(a_[m].tolist(), b_[m].tolist()):
        adj[x].add(y)
        adj[y].add(x)


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


def partition(pset, k, rng, minsz=1, maxsz=None):
    pset = list(pset)
    P = set(pset)
    seeds = [rng.choice(pset)]
    for _ in range(k - 1):
        cands = sorted(((min((cx[p] - cx[q]) ** 2 + (cy[p] - cy[q]) ** 2 for q in seeds), p)
                        for p in pset if p not in seeds), reverse=True)[:4]
        seeds.append(rng.choice(cands)[1])
    cap = math.ceil(len(pset) / k) + 1
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
    grp = collections.defaultdict(list)
    for p, r in own.items():
        grp[r].append(p)
    return [sorted(v) for v in grp.values()]


# 区域内均分 40（连通块按大小分州数；对角线矩形可能含多个连通海块）
blocks = comps(inside, adj)
print(f'区域内连通块: {[len(b) for b in blocks]}')
ks = [1] * len(blocks)
rem = K_IN - len(blocks)
if rem < 0:
    print('!! 连通块多于 40，中止'); sys.exit(1)
sizes = [len(b) for b in blocks]
while rem > 0:
    cand = [i for i in range(len(blocks)) if ks[i] < max(1, sizes[i] // 8)] or list(range(len(blocks)))
    i = max(cand, key=lambda i: sizes[i] / ks[i])
    ks[i] += 1
    rem -= 1
rng = __import__('random').Random(7)
groups = []
for i, blk in enumerate(blocks):
    if ks[i] == 1:
        groups.append(list(blk))
    else:
        groups.extend(partition(blk, ks[i], rng))
print(f'区域内分出 {len(groups)} 组: {[len(g) for g in groups]}')

NEW = 862
tpl = open(os.path.join(ST, '483-State_483.txt'), encoding='utf-8-sig', newline='').read()
TPL = re.sub(r'\bname\s*=\s*"[^"]*"', 'name="STATE_{sid}"', tpl)
TPL = re.sub(r'\t\towner\s*=\s*\w+\r\n', '', TPL)
TPL = re.sub(r'\r\n\t\tadd_core_of\s*=\s*\w+', '', TPL)
TPL = re.sub(r'victory_points\s*=\s*\{[^}]*\}\r\n', '', TPL)
TPL = re.sub(r'\t\t\t\d+ = \{\r\n(?:\t\t\t\t[^\r\n]*\r\n)+\t\t\t\}\r\n', '', TPL)
TPL = re.sub(r'manpower\s*=\s*\d+', 'manpower = 0', TPL)

bdir = os.path.join(ROOT, '.backups', 'sea_split_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)

def write_state(sid, provs, name_loc):
    body = TPL.replace('{sid}', str(sid))
    body = re.sub(r'(provinces\s*=\s*\{)[^}]*(\})',
                  lambda m: f'{m.group(1)}\r\n\t\t{" ".join(map(str, sorted(provs)))}\r\n\t{m.group(2)}', body)
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(body)
    return f' STATE_{sid}:0 "{name_loc}"'

loc_lines = []
for i, g in enumerate(sorted(groups, key=lambda g: g[0])):
    loc_lines.append(write_state(NEW + i, g, '*'))
outside_state = NEW + K_IN
loc_lines.append(write_state(outside_state, outside, '暗之外海'))
print(f'新州文件: {NEW}-{outside_state}（共 {K_IN + 1} 个）')

# 本地化追加
LOC = os.path.join(G, 'localisation', 'simp_chinese')
lp = os.path.join(LOC, 'DOT_state_names_gamma_l_simp_chinese.yml')
cur = open(lp, encoding='utf-8-sig', errors='replace').read()
open(lp, 'wb').write((cur.rstrip('\r\n') + '\r\n' + '\r\n'.join(loc_lines) + '\r\n').encode('utf-8'))
print('州名本地化已追加')

# 落地后全量同步 buildings
import subprocess
r = subprocess.run([sys.executable, os.path.join(ROOT, 'rebuild_buildings.py')],
                   cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
print(r.stdout[-700:] if r.returncode == 0 else f'!! buildings 失败\n{r.stdout[-500:]}')

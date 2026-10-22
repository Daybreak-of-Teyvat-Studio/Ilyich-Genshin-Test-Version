# -*- coding: utf-8 -*-
import os, io, re, sys, collections
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
Image.MAX_IMAGE_PIXELS = None
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
OUT = os.path.join(REPO, 'tools', 'frac_out.txt')
o = []

kind, rgb2id = {}, {}
for line in io.open(os.path.join(G, 'map', 'definition.csv'), 'rb').read().decode('utf-8-sig', errors='replace').splitlines():
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
s2p, p2s = {}, {}
sd = os.path.join(G, 'history', 'states')
for f in os.listdir(sd):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    if m:
        ps = [int(x) for x in m.group(1).split()]
        s2p[sid] = ps
        for p in ps:
            p2s[p] = sid
regions = {}
for f in sorted(os.listdir(os.path.join(G, 'map', 'strategicregions'))):
    t = io.open(os.path.join(G, 'map', 'strategicregions', f), 'rb').read().decode('utf-8-sig')
    rid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    regions[rid] = [int(x) for x in re.search(r'provinces=\{([^}]*)\}', t, re.S).group(1).split()]
p2r = {p: rid for rid, ps in regions.items() for p in ps}

o.append('===== 4679 及周边 =====')
for p in (4679, 4681, 4682, 4683, 4684, 3544, 5719, 6886, 6937, 7104, 7293, 7776):
    o.append(f'  p{p}: 类型={kind.get(p, "?")}, 州={p2s.get(p, "无")}, 区域={p2r.get(p, "无")}')

# 邻接（4 邻域像素）找出 4679 的邻居
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)

def neighbors(p):
    ys, xs = np.where(prov == p)
    nb = collections.Counter()
    for y, x in zip(ys[:4000], xs[:4000]):
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W:
                q = int(prov[yy, xx])
                if q and q != p:
                    nb[q] += 1
    return nb

for p in (4679, 5719, 6886):
    nb = neighbors(p)
    o.append('')
    o.append(f'p{p} 邻居 top12: ' + ', '.join(f'{q}({kind.get(q,"?")},州{s2p.get(q,"-")},区{p2r.get(q,"-")})×{c}' for q, c in nb.most_common(12)))

# 区域1 的连通块（用州/省邻接近似 → 简化：只查 4679 邻域是否全在其它区）
o.append('')
nb = neighbors(4679)
others = [q for q in nb if p2r.get(q) != 1]
o.append(f'4679 的邻居中不属于区域1的: {[(q, p2r.get(q), kind.get(q)) for q in others]}')

# 州62 文件全文
o.append('')
o.append('===== 州62 文件全文 =====')
t = io.open(os.path.join(sd, '62-State_62.txt'), 'rb').read()
o.append(repr(t.decode('utf-8-sig')))
# 对比：其它州 infrastructure=10 的写法
o.append('')
cnt = 0
for f in os.listdir(sd):
    if not f.endswith('.txt'):
        continue
    tt = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'infrastructure\s*=\s*(\d+)', tt)
    if m and int(m.group(1)) >= 10:
        cnt += 1
        if cnt <= 6:
            o.append(f'  {f}: infrastructure={m.group(1)}, category={re.search(r"state_category\s*=\s*(\w+)", tt).group(1) if re.search(r"state_category", tt) else "?"}')
o.append(f'  infrastructure>=10 的州共 {cnt} 个')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

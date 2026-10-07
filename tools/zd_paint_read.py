# -*- coding: utf-8 -*-
"""zd_paint_read.py —— 读至冬涂色图：连通色块 → 省分组
输出: tools/zd_division.json（省→新州组件映射 + 统计），只读不写 mod"""
import os, re, sys, glob, json, collections
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
PAINT = r'C:\Users\LR\Desktop\hoi4ra2mod\提瓦特黎明\Gamma至冬省图_双层.png'
OX, OY = 1562, 278          # PSD 裁剪原点（bbox 已含 40px 边距）
PALETTE = [(255, 0, 255), (0, 0, 255), (0, 255, 0), (255, 255, 0), (255, 0, 0)]
TOL = 100

# ---- SNE 州/省 ----
sne_states = {}
p2s = {}
for f in glob.glob(os.path.join(MOD, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in (pm.group(1).split() if pm else [])]
    for q in provs:
        p2s[q] = sid
    if om and om.group(1) == 'SNE':
        sne_states[sid] = provs
sne_provs = sorted({q for pv in sne_states.values() for q in pv})
sne_set = set(sne_provs)

# ---- 省像素（裁剪坐标） ----
rgb2id = {}
for line in open(os.path.join(MOD, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.strip().split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
arr = np.asarray(Image.open(os.path.join(MOD, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
sub = arr[OY:OY + 527, OX:OX + 821]
key = (sub[:, :, 0] << 16) | (sub[:, :, 1] << 8) | sub[:, :, 2]
id2rgb = {v: k for k, v in rgb2id.items()}
prov_pix = {}
for q in sne_provs:
    r, g, b = id2rgb[q]
    ys, xs = np.nonzero(key == ((r << 16) | (g << 8) | b))
    if len(ys):
        prov_pix[q] = (ys, xs)
missing_pix = [q for q in sne_provs if q not in prov_pix]
print(f'有像素的 SNE 省 {len(prov_pix)}/{len(sne_provs)}；缺像素 {missing_pix or "无"}')

# ---- 涂色层 ----
pim = np.asarray(Image.open(PAINT).convert('RGBA')).astype(np.int32)
ph, pw = pim.shape[:2]
print(f'涂色图: {pw}x{ph}')
pal = np.array(PALETTE)
rgbp = pim[:, :, :3]
alpha = pim[:, :, 3]
d2 = ((rgbp[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(axis=3)
nearest = d2.argmin(axis=2)
near_dist = np.take_along_axis(d2, nearest[:, :, None], axis=2)[:, :, 0]
painted = (alpha > 128) & (near_dist < TOL ** 2)
print(f'涂色像素 {int(painted.sum())}（alpha>128 且近调色板）')
label = np.full((ph, pw), -1, dtype=np.int32)
comp_color = {}
comp_id = 0
for ci in range(len(PALETTE)):
    cmask = painted & (nearest == ci)
    ys, xs = np.nonzero(cmask)
    seen = np.zeros_like(cmask, dtype=bool)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if seen[y0, x0]:
            continue
        stack = [(y0, x0)]
        seen[y0, x0] = True
        px = []
        while stack:
            y, x = stack.pop()
            px.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < ph and 0 <= nx < pw and cmask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        for (y, x) in px:
            label[y, x] = comp_id
        comp_color[comp_id] = PALETTE[ci]
        comp_id += 1
print(f'连通色块 {comp_id} 个')

# ---- 省 → 色块（多数决） ----
lab_flat = label.reshape(-1)
prov_comp, unpainted = {}, []
for q, (ys, xs) in prov_pix.items():
    labs = lab_flat[ys * pw + xs]
    labs = labs[labs >= 0]
    cov = len(labs) / len(ys)
    if cov < 0.10:
        unpainted.append(q)
        continue
    c, n = collections.Counter(labs.tolist()).most_common(1)[0]
    prov_comp[q] = (int(c), round(cov, 2))

comp_provs = collections.defaultdict(list)
for q, (c, _) in prov_comp.items():
    comp_provs[c].append(q)
print(f'\n已涂省 {len(prov_comp)}，未涂省 {len(unpainted)}: {unpainted}')
print(f'\n=== 色块清单（省数） ===')
for c in sorted(comp_provs):
    print(f'  块{c} {comp_color[c]}: {len(comp_provs[c])} 省')
tiny = [c for c, pv in comp_provs.items() if len(pv) < 2]
print(f'少于 2 省的色块: {tiny or "无"}')

# ---- 未涂省：挂到相邻省的多数色块 ----
pid_map = np.full((ph, pw), -1, dtype=np.int32)
for q, (ys, xs) in prov_pix.items():
    pid_map[ys, xs] = q
adj = collections.defaultdict(collections.Counter)
for dy, dx, swap in ((0, 1, False), (1, 0, False), (1, 1, False), (1, -1, True)):
    if swap:
        A = pid_map[:ph - dy, -dx:]
        B = pid_map[dy:, :pw + dx]
    else:
        A = pid_map[:ph - dy, :pw - dx]
        B = pid_map[dy:, dx:]
    m = (A >= 0) & (B >= 0) & (A != B)
    for u, v in zip(A[m].tolist(), B[m].tolist()):
        adj[u][v] += 1
        adj[v][u] += 1
for q in unpainted:
    nb = [p for p, _ in sorted(adj.get(q, {}).items(), key=lambda kv: -kv[1]) if p in prov_comp]
    if nb:
        c = prov_comp[nb[0]][0]
        prov_comp[q] = (c, 0.0)
        comp_provs[c].append(q)
        print(f'  未涂省 p{q} → 块{c}（邻接多数：{nb[:4]}）')
    else:
        print(f'  !! 未涂省 p{q} 无已涂邻省，人工处理')

# ---- 保存 ----
out = {
    'offset': [OX, OY],
    'comp_color': {str(c): comp_color[c] for c in comp_provs},
    'comp_provs': {str(c): sorted(v) for c, v in comp_provs.items()},
    'prov_comp': {str(q): prov_comp[q][0] for q in prov_comp},
}
with open(os.path.join(ROOT, 'tools', 'zd_division.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"\n共 {len(comp_provs)} 个新州组件，映射已存 tools/zd_division.json")

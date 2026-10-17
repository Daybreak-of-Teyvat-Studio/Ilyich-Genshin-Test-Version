# -*- coding: utf-8 -*-
import os, io, re, sys, datetime, collections
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
Image.MAX_IMAGE_PIXELS = None
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
BK = os.path.join(REPO, '.backups', 'mega014_20261014_220448', '仓库_buildings.txt')
OUT = os.path.join(REPO, 'tools', 'blddiag_out.txt')
o = []

fp = os.path.join(G, 'map', 'buildings.txt')
raw = io.open(fp, 'rb').read()
mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
o.append(f'当前 buildings.txt: {len(raw)}B, mtime={mt:%m-%d %H:%M:%S}')
o.append(f'尾部 40B: {raw[-40:]!r}')
bkraw = io.open(BK, 'rb').read()
bkmt = datetime.datetime.fromtimestamp(os.path.getmtime(BK))
o.append(f'备份(mega014前) buildings.txt: {len(bkraw)}B, mtime={bkmt:%m-%d %H:%M:%S}, 尾 20B={bkraw[-20:]!r}')

nl = b'\r\n' if b'\r\n' in raw else b'\n'
lines = raw.split(nl)
bkl = bkraw.split(b'\r\n' if b'\r\n' in bkraw else b'\n')
o.append(f'当前 {len(lines)} 行, 备份 {len(bkl)} 行')

# 14 行：备份里对应行（同坐标）是否也错
PROB = [(38378, 35, 14, 2348), (38415, 434, 44, 1646), (38416, 434, 44, 1646), (38417, 434, 44, 1646),
        (38492, 254, 119, 1604), (38601, 114, 192, 77), (38619, 176, 206, 1410), (38668, 156, 252, 4396),
        (38806, 51, 439, 2453), (38807, 456, 440, 1122), (38808, 456, 440, 1122), (38853, 504, 490, 3554),
        (38906, 584, 595, 1273), (38907, 584, 595, 1273)]
o.append('')
o.append('===== 14 行：当前 vs 备份（同坐标行） =====')
bkset = {}
for l in bkl:
    f = l.decode('utf-8', 'replace').split(';')
    if len(f) == 7:
        bkset[(f[1], f[2], f[4])] = l.decode('utf-8', 'replace')
for ln, sup, was, prov in PROB:
    cur = lines[ln - 1].decode('utf-8', 'replace')
    f = cur.split(';')
    old = bkset.get((f[1], f[2], f[4]))
    o.append(f'  L{ln} 当前: {cur[:70]}')
    o.append(f'        备份: {old[:70] if old else "（备份无同坐标行）"}')

# 像素→省→州 验证（用游戏规则：像素所在省；海省则最近陆地）
kind = {}
rgb2id = {}
for line in io.open(os.path.join(G, 'map', 'definition.csv'), 'rb').read().decode('utf-8-sig', errors='replace').splitlines():
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4]
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
s2p = {}
for f in os.listdir(os.path.join(G, 'history', 'states')):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(G, 'history', 'states', f), 'rb').read().decode('utf-8-sig', errors='replace')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    if m:
        for p in m.group(1).split():
            s2p[int(p)] = sid

def at(l):
    f = l.decode('utf-8', 'replace').split(';')
    x, z = float(f[2]), float(f[4])
    px, py = int(round(x)), int(round(H - z))
    return (f, int(prov[py, px]) if 0 <= py < H and 0 <= px < W else -1)

o.append('')
o.append('===== 14 行像素省/州 复核（应与 nudge 的 was 一致） =====')
for ln, sup, was, prov0 in PROB:
    f, p = at(lines[ln - 1])
    o.append(f'  L{ln}: 坐标({f[2]},{f[4]}) → 像素省={p} ({kind.get(p, "?")}) → 州={s2p.get(p, "无")} | nudge: 期望{sup} was{was}')

o.append('')
o.append('===== 8 个宫殿行像素省/州 =====')
for i in range(39107, 39115):
    l = lines[i - 1].decode('utf-8', 'replace')
    body = l.lstrip('#')
    fb = body.split(';')
    x, z = float(fb[2]), float(fb[4])
    px, py = int(round(x)), int(round(H - z))
    p = int(prov[py, px])
    o.append(f'  L{i}: {l[:60]} → 像素省={p} ({kind.get(p, "?")}) → 州={s2p.get(p, "无")}')

o.append('')
o.append('===== 重复行检查 =====')
cnt = collections.Counter(l.decode('utf-8', 'replace') for l in lines if l.strip())
dups = [(k, v) for k, v in cnt.items() if v > 1]
for k, v in dups[:10]:
    o.append(f'  ×{v}: {k[:80]}')
o.append(f'  重复行种类 {len(dups)}')
o.append(f'  空行位置: {[i + 1 for i, l in enumerate(lines) if not l.strip()]}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

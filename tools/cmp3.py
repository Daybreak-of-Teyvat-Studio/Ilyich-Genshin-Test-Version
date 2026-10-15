import os, io, hashlib

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\cmp3_out.txt'
o = []

CONFIGS = ['default.map', 'continent.txt', 'adjacencies.csv', 'adjacency_rules.txt',
           'seasons.txt', 'weatherpositions.txt', 'colors.txt', 'ambient_object.txt',
           'unitstacks.txt', 'supply_nodes.txt', 'railways.txt', 'cities.txt',
           'buildings_landmark.txt', 'airports.txt', 'rocketsites.txt']
BMPS = ['provinces.bmp', 'terrain.bmp', 'heightmap.bmp', 'rivers.bmp', 'trees.bmp',
        'cities.bmp', 'world_normal.bmp', 'colormap_rgb.bmp', 'colormap_water.bmp']

for name in CONFIGS:
    o.append(f'===== {name} =====')
    for label, root in [('Gamma', G), ('Beta', B), ('原版', V)]:
        fp = os.path.join(root, 'map', name)
        if not os.path.exists(fp):
            o.append(f'  [{label}] 不存在')
            continue
        sz = os.path.getsize(fp)
        if sz <= 4096:
            t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
            body = t.strip()
            if len(body) > 900:
                body = body[:900] + ' ...'
            o.append(f'  [{label}] {sz}B:')
            for l in body.splitlines()[:40]:
                o.append(f'      {l[:190]}')
        else:
            o.append(f'  [{label}] {sz}B (大文件，跳过内容)')
    o.append('')

o.append('===== BMP 三版对照（尺寸/位深/大小） =====')
for name in BMPS:
    o.append(f'  {name}:')
    for label, root in [('Gamma', G), ('Beta', B), ('原版', V)]:
        fp = os.path.join(root, 'map', name)
        if not os.path.exists(fp):
            o.append(f'    [{label}] 不存在')
            continue
        import struct
        with io.open(fp, 'rb') as f:
            h = f.read(30)
        w, ht = struct.unpack('<ii', h[18:26])
        bpp = struct.unpack('<H', h[28:30])[0]
        o.append(f'    [{label}] {w}x{ht} {bpp}bpp {os.path.getsize(fp)}B')
o.append('')

o.append('===== map 目录文件清单 三版对照 =====')
def names(root):
    d = os.path.join(root, 'map')
    return set(os.listdir(d)) if os.path.isdir(d) else set()
ng, nb, nv = names(G), names(B), names(V)
o.append(f'  Gamma 独有: {sorted(ng - nb - nv)}')
o.append(f'  Beta 独有(相对原版): {sorted(nb - nv)}')
o.append(f'  Gamma 缺(原版有 Gamma 无): {sorted(nv - ng)}')
o.append(f'  Gamma 缺(Beta 有 Gamma 无): {sorted(nb - ng)}')
o.append(f'  三版都有: {len(ng & nb & nv)} 个')
o.append('')
o.append(f'  Gamma map/ 全部: {sorted(ng)}')
o.append(f'  Beta  map/ 全部: {sorted(nb)}')
o.append(f'  原版  map/ 全部: {sorted(nv)}')

# default.map 的 max_provinces 与 definition.csv 行数对照
o.append('')
o.append('===== max_provinces vs definition.csv =====')
import re
for label, root in [('Gamma', G), ('Beta', B), ('原版', V)]:
    fp = os.path.join(root, 'map', 'default.map')
    mp = 'N/A'
    if os.path.exists(fp):
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        m = re.search(r'max_provinces\s*=\s*(\d+)', t)
        mp = m.group(1) if m else '未找到'
    dfp = os.path.join(root, 'map', 'definition.csv')
    lines = 0
    if os.path.exists(dfp):
        raw = io.open(dfp, 'rb').read()
        lines = raw.count(b'\n') + (0 if raw.endswith(b'\n') else 1)
    o.append(f'  [{label}] max_provinces={mp}, definition.csv 行数={lines}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

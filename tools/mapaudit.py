import os, io, struct, hashlib, datetime

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
VAN = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\mapaudit_out.txt'
o = []

def bmp_info(fp):
    with io.open(fp, 'rb') as f:
        h = f.read(54)
    if len(h) < 54 or h[:2] != b'BM':
        return f'(非 BMP, 前 16B={h[:16]!r})'
    size = struct.unpack('<I', h[2:6])[0]
    off = struct.unpack('<I', h[10:14])[0]
    w, ht = struct.unpack('<ii', h[18:26])
    bpp = struct.unpack('<H', h[28:30])[0]
    return f'{w}x{ht} {bpp}bpp dataoff={off} filesize={os.path.getsize(fp)}(头写{size})'

MAPFILES = ['definition.csv', 'provinces.bmp', 'terrain.bmp', 'heightmap.bmp', 'rivers.bmp',
            'positions.txt', 'buildings.txt', 'airports.txt', 'rocketsites.txt',
            'supply_nodes.txt', 'railways.txt', 'unitstacks.txt', 'cities.txt',
            'adjacencies.csv', 'continent.txt', 'default.map', 'climate.txt',
            'trees.bmp', 'colormap_rgb.bmp', 'colormap_water.bmp', 'islands.txt', 'lakes.txt',
            'seasons.txt', 'weatherpositions.txt', 'unitstackpositions.txt', 'mapdefault.txt']

o.append('===== 仓库 map/ 文件体检 =====')
md = os.path.join(REPO, 'map')
for f in MAPFILES:
    fp = os.path.join(md, f)
    if not os.path.exists(fp):
        continue
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    sz = os.path.getsize(fp)
    info = ''
    if f.endswith('.bmp'):
        info = bmp_info(fp)
    else:
        raw = io.open(fp, 'rb').read()
        info = f'{sz}B, 行数={raw.count(bytes([10]))}'
    o.append(f'  {f:22s} {mt:%Y-%m-%d %H:%M}  {info}')

o.append('')
o.append('===== map 目录全部文件（含子目录文件数） =====')
for dirpath, dirnames, filenames in os.walk(md):
    rel = os.path.relpath(dirpath, md)
    if filenames:
        o.append(f'  {rel}/: {len(filenames)} 文件')
        if rel == '.':
            for f in sorted(filenames):
                fp = os.path.join(dirpath, f)
                o.append(f'      {f}  {os.path.getsize(fp)}B')

o.append('')
o.append('===== 仓库 vs 副本 map 全部文件哈希一致性 =====')
md2 = os.path.join(DEPL, 'map')
diff = []
for dirpath, dirnames, filenames in os.walk(md):
    for f in filenames:
        a = os.path.join(dirpath, f)
        b = os.path.join(md2, os.path.relpath(a, md))
        if not os.path.exists(b):
            diff.append(('缺于副本', os.path.relpath(a, md)))
            continue
        if hashlib.md5(io.open(a, 'rb').read()).hexdigest() != hashlib.md5(io.open(b, 'rb').read()).hexdigest():
            diff.append(('内容不同', os.path.relpath(a, md)))
# 副本多出的文件
for dirpath, dirnames, filenames in os.walk(md2):
    for f in filenames:
        a = os.path.join(dirpath, f)
        if not os.path.exists(os.path.join(md, os.path.relpath(a, md2))):
            diff.append(('仅副本有', os.path.relpath(a, md2)))
o.append(f'  差异: {diff if diff else "无 ✓"}')

o.append('')
o.append('===== 原版对照 =====')
vmd = os.path.join(VAN, 'map')
for f in ['provinces.bmp', 'terrain.bmp', 'heightmap.bmp', 'rivers.bmp', 'definition.csv']:
    fp = os.path.join(vmd, f)
    if os.path.exists(fp):
        o.append(f'  原版 {f}: {bmp_info(fp) if f.endswith(".bmp") else str(os.path.getsize(fp)) + "B"}')

o.append('')
o.append('===== definition.csv 抽查（仓库） =====')
fp = os.path.join(md, 'definition.csv')
raw = io.open(fp, 'rb').read()
t = raw.decode('utf-8-sig', errors='replace')
lines = t.splitlines()
o.append(f'  行数 {len(lines)}; 首行: {lines[0][:120]}')
o.append(f'  末行: {lines[-1][:120]}')
bad = [i for i, l in enumerate(lines, 1) if l.strip() and len(l.split(';')) < 6]
o.append(f'  字段<6 的行: {bad[:10] if bad else "无 ✓"}')
o.append(f'  结尾字节: {raw[-8:]!r}, 有尾换行={raw.endswith(bytes([10]))}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

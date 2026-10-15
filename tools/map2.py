import os, io, struct, hashlib, glob

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
BK = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\map2_out.txt'
o = []

# 1) railways.txt 格式对照
o.append('===== railways.txt 格式（原版/Beta 前 6 行） =====')
for label, root in [('原版', V), ('Beta', B), ('Gamma', G)]:
    fp = os.path.join(root, 'map', 'railways.txt')
    if not os.path.exists(fp):
        o.append(f'  [{label}] 不存在')
        continue
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    lines = t.splitlines()
    o.append(f'  [{label}] {os.path.getsize(fp)}B, {len(lines)} 行')
    for l in lines[:6]:
        p = l.split()
        o.append(f'      {l[:150]}')
        if len(p) >= 2 and p[1].isdigit():
            o.append(f'        → 字段 {len(p)}, 声明点数 {p[1]}, 期望字段 {2 + 2*int(p[1])}')
    # 全文件逐行校验
    bad = []
    for i, l in enumerate(lines, 1):
        if not l.strip():
            continue
        p = l.split()
        if len(p) >= 2 and p[0].isdigit() and p[1].isdigit():
            exp = 2 + 2 * int(p[1])
            if len(p) != exp:
                bad.append((i, len(p), exp))
    o.append(f'      行字段数不符: {bad[:6]}{" ...共" + str(len(bad)) if len(bad) > 6 else ""}' if bad else '      行字段数全对 ✓')
o.append('')

# 2) supply_nodes.txt 格式对照
o.append('===== supply_nodes.txt 格式（前 8 行） =====')
for label, root in [('原版', V), ('Beta', B), ('Gamma', G)]:
    fp = os.path.join(root, 'map', 'supply_nodes.txt')
    if not os.path.exists(fp):
        o.append(f'  [{label}] 不存在')
        continue
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    lines = [l for l in t.splitlines() if l.strip()]
    o.append(f'  [{label}] {os.path.getsize(fp)}B, {len(lines)} 行')
    for l in lines[:8]:
        o.append(f'      {l[:150]}')
o.append('')

# 3) map/ 与 map/terrain/ 下所有 DDS 头部（宽高/格式）
o.append('===== DDS 贴图头部（map/ 与 map/terrain/） =====')
for label, root in [('Gamma', G), ('Beta', B), ('原版', V)]:
    o.append(f'--- {label} ---')
    for sub in ('', 'terrain'):
        d = os.path.join(root, 'map', sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith('.dds'):
                continue
            fp = os.path.join(d, f)
            with io.open(fp, 'rb') as fh:
                h = fh.read(128)
            if h[:4] != b'DDS ':
                o.append(f'    {sub}/{f}: 非 DDS 头! 前 16B={h[:16]!r} ({os.path.getsize(fp)}B)')
                continue
            height, width = struct.unpack('<II', h[12:20])
            mip = struct.unpack('<I', h[28:32])[0]
            fmt = h[84:88]
            pf = struct.unpack('<I', h[80:84])[0]
            o.append(f'    {sub}/{f}: {width}x{height} mip={mip} fmt={fmt!r} pfFlags={pf} {os.path.getsize(fp)}B')
o.append('')

# 4) map/terrain/ 三版文件清单
o.append('===== map/terrain/ 文件清单 三版对照 =====')
def ls(root):
    d = os.path.join(root, 'map', 'terrain')
    return set(os.listdir(d)) if os.path.isdir(d) else set()
sg, sb, sv = ls(G), ls(B), ls(V)
o.append(f'  Gamma: {sorted(sg)}')
o.append(f'  Beta:  {sorted(sb)}')
o.append(f'  原版:  {sorted(sv)}')
o.append(f'  Gamma 独有 vs Beta: {sorted(sg - sb)}')
o.append(f'  Gamma 独有 vs 原版: {sorted(sg - sv)}')
o.append(f'  Beta/原版有 Gamma 无: {sorted((sb | sv) - sg)}')
o.append('')

# 5) 备份里找 railways/supply_nodes/colormap 的旧版本
o.append('===== 备份中的旧版本（railways/supply_nodes/colormap/terrain 相关） =====')
pats = ('railways', 'supply_nodes', 'colormap', 'heightmap_01', 'world_normal_0', 'terrain_0', 'DOT MAP')
found = {}
for bkd in sorted(glob.glob(os.path.join(BK, '*')), key=os.path.getmtime, reverse=True):
    if not os.path.isdir(bkd):
        continue
    for root2, dirs2, files2 in os.walk(bkd):
        for f in files2:
            fl = f.lower()
            if any(p.lower() in fl for p in pats):
                key = f
                found.setdefault(key, []).append((os.path.basename(bkd), os.path.join(root2, f)))
for k in sorted(found):
    o.append(f'  {k}: {len(found[k])} 个备份副本')
    for bkn, p in found[k][:4]:
        o.append(f'      {bkn}  {os.path.getsize(p)}B md5={hashlib.md5(io.open(p,"rb").read()).hexdigest()[:8]}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

import os, io, hashlib, datetime, glob, shutil

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
BK = os.path.join(REPO, '.backups')
OUT = os.path.join(REPO, 'tools', 'mapdiff_out.txt')
o = []

# 1) 所有备份目录（按时间）
o.append('===== 备份目录（新→旧） =====')
bks = sorted([d for d in glob.glob(os.path.join(BK, '*')) if os.path.isdir(d)],
             key=os.path.getmtime, reverse=True)
for d in bks:
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(d))
    o.append(f'  {os.path.basename(d)}  {mt:%m-%d %H:%M}')
    # 它含哪些 map 文件
    maps = []
    for root2, dirs2, files2 in os.walk(d):
        for f in files2:
            if f.endswith(('.map', '.csv', '.bmp')) or f in ('railways.txt', 'supply_nodes.txt',
                                                              'airports.txt', 'rocketsites.txt', 'buildings.txt',
                                                              'unitstacks.txt', 'positions.txt', 'weatherpositions.txt'):
                maps.append(os.path.relpath(os.path.join(root2, f), d))
    if maps:
        o.append(f'      map 相关: {sorted(set(maps))}')
o.append('')

# 2) 当前 repo map/ 每个文件：mtime + 与最近备份的差异
o.append('===== 当前 map/ 文件 mtime 与备份对比 =====')
md = os.path.join(G, 'map')
targets = []
for root2, dirs2, files2 in os.walk(md):
    for f in files2:
        targets.append(os.path.relpath(os.path.join(root2, f), md))

def find_in_backups(rel):
    """在备份里找同名文件（按 basename 匹配），返回 (备份名, 路径) 列表，新→旧"""
    base = os.path.basename(rel)
    res = []
    for d in bks:
        for root3, dirs3, files3 in os.walk(d):
            for f in files3:
                if f == base or f.endswith('_' + base) or f == base.replace('.bmp', '.bmp'):
                    res.append((os.path.basename(d), os.path.join(root3, f)))
    return res

for rel in sorted(targets):
    fp = os.path.join(md, rel)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    cur = io.open(fp, 'rb').read()
    h = hashlib.md5(cur).hexdigest()[:8]
    cands = find_in_backups(rel)
    line = f'  {rel:28s} mtime={mt:%Y-%m-%d %H:%M} md5={h} size={len(cur)}'
    if cands:
        same = []
        diff = []
        for bkn, bp in cands:
            bh = hashlib.md5(io.open(bp, 'rb').read()).hexdigest()[:8]
            (same if bh == h else diff).append(f'{bkn}({bh})')
        line += f' | 备份不同: {diff[:3]}' if diff else f' | 备份一致: {len(same)}个'
    o.append(line)

# 3) railways/supply_nodes/weatherpositions 全文 + 备份对照
o.append('')
o.append('===== 重点文件内容 =====')
for rel in ['railways.txt', 'supply_nodes.txt', 'weatherpositions.txt', 'adjacencies.csv']:
    fp = os.path.join(md, rel)
    if not os.path.exists(fp):
        continue
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    o.append(f'--- {rel} ({len(t)} 字符) ---')
    for l in t.splitlines()[:12]:
        o.append('    ' + l[:190])
    if rel == 'railways.txt':
        # 校验：每行 = 等级 点数 然后 点数*2 个坐标
        for i, l in enumerate(t.splitlines(), 1):
            p = l.split()
            if len(p) >= 2:
                o.append(f'    行{i}: 字段{len(p)}, 声明点数={p[1]}, 需要字段={2 + 2*int(p[1]) if p[1].isdigit() else "?"}')
    # 备份里的同名文件
    cands = find_in_backups(rel)
    for bkn, bp in cands[:3]:
        bt = io.open(bp, 'rb').read()
        o.append(f'    [备份 {bkn}] {len(bt)}B, md5={hashlib.md5(bt).hexdigest()[:8]}')
        btt = bt.decode('utf-8-sig', errors='replace')
        for l in btt.splitlines()[:4]:
            o.append('        ' + l[:170])

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

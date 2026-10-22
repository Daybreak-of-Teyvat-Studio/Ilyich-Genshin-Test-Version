import os, io

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\nodecheck_out.txt'
o = []

def defs(root):
    kind = {}
    for line in io.open(os.path.join(root, 'map', 'definition.csv'), 'rb').read().decode('utf-8-sig', errors='replace').splitlines():
        a = line.split(';')
        if len(a) > 4 and a[0].strip().isdigit():
            kind[int(a[0])] = a[4].strip()
    return kind

kg = defs(G)
kb = defs(B)
land_g = {p for p, k in kg.items() if k == 'land'}
sea_g = {p for p, k in kg.items() if k != 'land'}
o.append(f'Gamma definition.csv: {len(kg)} 省, 陆 {len(land_g)}, 非陆 {len(sea_g)}, max={max(kg)}')

# 1) supply_nodes
o.append('')
o.append('===== supply_nodes.txt（Gamma 126 条）逐条复验 =====')
t = io.open(os.path.join(G, 'map', 'supply_nodes.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
sn = []
for l in t.splitlines():
    p = l.split()
    if len(p) == 2 and p[1].isdigit():
        sn.append(int(p[1]))
missing = [x for x in sn if x not in kg]
sea = [x for x in sn if x in sea_g]
o.append(f'  条目 {len(sn)}；不在 definition 的: {missing if missing else "无 ✓"}')
o.append(f'  落在海/非陆省的: {sea if sea else "无 ✓"}')
# 与 Beta 列表对照
tb = io.open(os.path.join(B, 'map', 'supply_nodes.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
snb = [int(l.split()[1]) for l in tb.splitlines() if len(l.split()) == 2 and l.split()[1].isdigit()]
o.append(f'  Gamma 是 Beta 列表的子集? {set(sn) <= set(snb)}；Beta 有 Gamma 无: {sorted(set(snb)-set(sn))[:20]}')
o.append(f'  Beta 列表本身在其地图上非法? {[x for x in snb if x not in kb][:10]}')

# 2) railways
o.append('')
o.append('===== railways.txt 省号复验 =====')
t = io.open(os.path.join(G, 'map', 'railways.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
for i, l in enumerate(t.splitlines(), 1):
    if not l.strip():
        continue
    p = l.split()
    lvl, n = p[0], int(p[1]) if p[1].isdigit() else -1
    provs = [int(x) for x in p[2:] if x.lstrip('-').isdigit()]
    bad = [x for x in provs if x not in kg]
    seap = [x for x in provs if x in sea_g]
    o.append(f'  行{i}: 等级{lvl} 声明{n} 实际{len(provs)} | 不存在的省: {bad if bad else "无 ✓"} | 非陆省: {seap if seap else "无 ✓"}')
    o.append(f'        省号: {provs}')

# 3) weatherpositions
o.append('')
o.append('===== weatherpositions.txt（按战略区 id 键） =====')
t = io.open(os.path.join(G, 'map', 'weatherpositions.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
o.append('  内容: ' + t.replace('\n', ' | '))
# 战略区 id 列表
sd = os.path.join(G, 'map', 'strategicregions')
for f in sorted(os.listdir(sd)):
    tt = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    import re
    m = re.search(r'id\s*=\s*(\d+)', tt)
    o.append(f'  区域文件 {f}: id={m.group(1) if m else "?"}  weather={"有" if "weather" in tt else "【无】"}')

# 4) buildings_landmark.txt
o.append('')
o.append('===== buildings_landmark.txt 省号复验 =====')
t = io.open(os.path.join(G, 'map', 'buildings_landmark.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
for l in t.splitlines():
    if not l.strip():
        continue
    p = l.split(';')
    pid = int(p[0]) if p[0].strip().isdigit() else -1
    o.append(f'  {l[:80]}  → 省 {pid}: 存在={pid in kg}, 类型={kg.get(pid, "?")}')

# 5) 全 map/ 里所有"省号化"文件的一致性快扫：找出任何指向不存在省的条目
o.append('')
o.append('===== 其他含省号的地图文件抽查 =====')
for f in ('cities.txt', 'continent.txt', 'adjacencies.csv'):
    fp = os.path.join(G, 'map', f)
    if os.path.exists(fp):
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        nums = set()
        import re
        for m in re.finditer(r'\b(\d{1,5})\b', t):
            v = int(m.group(1))
            if v > 0:
                nums.add(v)
        bad = sorted(x for x in nums if x not in kg and x > 10)
        o.append(f'  {f}: 出现的数字中不在 definition 的: {bad[:15] if bad else "无 ✓"}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

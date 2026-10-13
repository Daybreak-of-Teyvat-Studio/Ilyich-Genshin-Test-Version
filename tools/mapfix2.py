# -*- coding: utf-8 -*-
"""mapfix2.py —— 地图定义修复包 + 海军变体修复（DRY 默认，--apply 应用）
A) buildings.txt：120 行（引擎 679×9 + 716×111）坐标挪进声明州陆地
B) buildings.txt：删除尾部 125 个空行（\r\n\r\n → \r\n）
C) buildings.txt：41 个海洋州补 spawn 行（照 beta 结构集）
D) 海军变体：INA cru_2 变体重名改唯一名+同步2舰；FAV heavy_2 去 front_1_custom_slot；FAV 文件完整性
E) 只读报告：41 海州 manpower / INA+FAV 全部舰船 version_name
"""
import os, re, sys, glob, struct, shutil, datetime, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
COPIES = [('仓库', G),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'mapfix2_{stamp}')
os.makedirs(BD, exist_ok=True)

# ============ 基础数据 ============
gk, colors = {}, {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            pid = int(c[0])
        except ValueError:
            continue
        gk[pid] = c[4]
        colors[(int(c[1]), int(c[2]), int(c[3]))] = pid

raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
W, H = struct.unpack('<ii', raw[18:26])
RB = W * 3
PIX = raw[off:]

def px(x, z):
    i = z * RB + x * 3
    return colors.get((PIX[i + 2], PIX[i + 1], PIX[i]))

# 州 → 省
s2p = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        s2p[int(m.group(1))] = [int(x) for x in re.findall(r'\d+', m2.group(1))]

# 全图 interior 采样（step2 + 8邻同省）
print('构建 interior 采样…')
prov_int = collections.defaultdict(list)
for z in range(1, H - 1, 2):
    for x in range(1, W - 1, 2):
        p = px(x, z)
        if p is None or len(prov_int[p]) >= 300:
            continue
        if all(px(x + dx, z + dz) == p for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
            prov_int[p].append((x, z))
state_int = collections.defaultdict(list)
for p, pts in prov_int.items():
    st = None
    for s, provs in s2p.items():
        if p in provs:
            st = s
            break
    if st is not None:
        state_int[st].extend([(x, z, p) for (x, z) in pts])
print(f'  interior 省 {len(prov_int)} / 州 {len(state_int)}')

def nearest_interior(st, x0, z0):
    best = None
    for (x, z, p) in state_int.get(st, []):
        d = abs(x - x0) + abs(z - z0)
        if best is None or d < best[0]:
            best = (d, x, z, p)
    return best

# ============ A+B) buildings.txt ============
L679 = [1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 3192]
L716 = [8009, 8013, 15210, 15217, 15230, 15233, 16006, 16100, 16662, 16749, 17028, 17031, 17036,
        17052, 17157, 17512, 17513, 17528, 17534, 17637, 17680, 17774, 17778, 18005, 18071, 18084,
        18099, 18173, 18414, 18509, 18546, 18555, 18588, 18630, 18647, 18771, 18772, 18773, 18775,
        18777, 18788, 18918, 18939, 19109, 19126, 19137, 19672, 19673, 20206, 20377, 20398, 20406,
        20879, 20880, 20887, 20904, 24800, 24802, 25977, 25984, 26304, 26645, 28720, 29804, 31945,
        32930, 33548, 33935, 34283, 35273, 35675, 35855, 35980, 36066, 37005, 37968, 38134, 38476,
        38541, 38672, 38762, 38806, 38807, 38808, 38884, 38920, 38921, 38963, 39064, 39106, 39140,
        39191, 39226, 39256, 39273, 39294, 39399, 39415, 39691, 39749, 39751, 39769, 39771, 39772,
        39891, 40073, 40132, 40133, 40552, 40584, 40585]
BAD = sorted(set(L679 + L716))

def fix_buildings(base, tag):
    p = os.path.join(base, 'map', 'buildings.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    lines = t.split('\n')
    nfix, fails = 0, []
    for ln in BAD:
        idx = ln - 1
        row = lines[idx].rstrip('\r')
        c = row.split(';')
        if len(c) < 7:
            fails.append((ln, 'parse', row[:60]))
            continue
        st = int(c[0])
        x0, z0 = int(float(c[2])), int(float(c[4]))
        got = nearest_interior(st, x0, z0)
        if got is None:
            fails.append((ln, 'no-interior', f'state={st}'))
            continue
        d, x1, z1, prov = got
        # 验证
        chk = px(x1, z1)
        if not (chk == prov and prov in s2p.get(st, [])):
            fails.append((ln, 'verify', f'{chk} vs {prov} vs state {st}'))
            continue
        c[2] = f'{x1}.00'
        c[4] = f'{z1}.00'
        lines[idx] = ';'.join(c)
        nfix += 1
        if nfix <= 5:
            print(f'    {tag} L{ln} s{st}: ({x0},{z0})→({x1},{z1}) 省{prov} 移距{d}')
    # B) 空行
    nb = sum(1 for l in lines if not l.strip())
    lines2 = [l for l in lines if l.strip()]
    t2 = '\r\n'.join(lines2) + '\r\n'
    print(f'  {tag}: 坐标修复 {nfix}/{len(BAD)} (失败 {len(fails)}), 空行移除 {nb}')
    for f in fails:
        print(f'    ★失败 {f}')
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_buildings.txt'))
        open(p, 'wb').write(t2.encode('utf-8'))
    return t2, nfix, nb, fails

print('=' * 60)
print('【A+B】buildings.txt 坐标修复 + 空行清理')
BASE_TXT = {}
for tag, base in COPIES:
    t2, nfix, nb, fails = fix_buildings(base, tag)
    BASE_TXT[tag] = (base, t2)

# ============ C) 海洋州补行 ============
print()
print('=' * 60)
print('【C】海洋州 spawn 行补充')
# beta 海州使用的类型集
btypes = collections.Counter()
for l in open(os.path.join(B, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 2:
        try:
            st = int(c[0])
        except ValueError:
            continue
        if 700 <= st <= 740:
            btypes[c[1].strip()] += 1
print(f'  beta 700-740 行类型: {dict(btypes)}')
# 采用与 317 被忽略的 8 类完全一致的集合（现版本有效类型；排除已废弃的 naval_base/rocket_site/nuclear_reactor）
SEA_TYPES = ['air_base', 'fuel_silo', 'radar_station', 'nuclear_reactor_spawn',
             'rocket_site_spawn', 'synthetic_refinery', 'stronghold_network', 'anti_air_building']
print(f'  采用类型集（与 317 被忽略的 8 类一致）: {SEA_TYPES}')
# 只读核对：beta 海州是否包含陆地省（决定 beta 的设计）
btmp = open(os.path.join(B, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read()
bk = {}
for l in btmp.split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            bk[int(c[0])] = c[4]
        except ValueError:
            pass
for sid in (700, 701, 702):
    f = os.path.join(B, 'history', 'states', f'STATE-{sid}.txt')
    if os.path.exists(f):
        t700 = open(f, encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t700)
        if m:
            ps = [int(x) for x in re.findall(r'\d+', m.group(1))]
            lands = [p for p in ps if bk.get(p) == 'land']
            print(f'  beta {sid} 州: {len(ps)} 省, 陆地省 {lands[:10]} (共 {len(lands)})')

# gamma 海州
g_sea = sorted(s for s, provs in s2p.items() if provs and all(gk.get(p) == 'sea' for p in provs))
# 每个海州的选址省：来自 airports.txt（我们生成的）
air_txt = open(os.path.join(G, 'map', 'airports.txt'), encoding='utf-8-sig', errors='replace').read()
site_of = {}
for m in re.finditer(r'(\d+)\s*=\s*\{([^}]*)\}', air_txt):
    sid = int(m.group(1))
    ps = [int(x) for x in re.findall(r'\d+', m.group(2))]
    if ps:
        site_of[sid] = ps[0]

new_rows = []
miss = []
for s in g_sea:
    site = site_of.get(s)
    if site is None:
        miss.append(s)
        continue
    pts = prov_int.get(site) or []
    x1 = z1 = None
    if pts:
        x1, z1 = pts[len(pts) // 2]
    if x1 is None:
        # 放宽：该省任意采样点
        for z in range(1, H - 1, 2):
            for x in range(1, W - 1, 2):
                if px(x, z) == site:
                    x1, z1 = x, z
                    break
            if x1 is not None:
                break
    if x1 is None or px(x1, z1) != site:
        miss.append(s)
        continue
    for ty in SEA_TYPES:
        new_rows.append(f'{s};{ty};{x1}.00;9.50;{z1}.00;0.00;0')
print(f'  海州 {len(g_sea)} 个, 补行 {len(new_rows)} 条, 无解 {miss}')
# 展示每个海州的选址省与坐标（前 6 个）
shown = 0
for s in g_sea:
    site = site_of.get(s)
    pts = prov_int.get(site) or []
    if pts and shown < 6:
        x1, z1 = pts[len(pts) // 2]
        print(f'    s{s}: 选址省 {site} 坐标 ({x1},{z1})')
        shown += 1
if new_rows:
    for tag, (base, t2) in BASE_TXT.items():
        p = os.path.join(base, 'map', 'buildings.txt')
        if APPLY:
            t3 = t2.rstrip('\r\n') + '\r\n' + '\r\n'.join(new_rows) + '\r\n'
            open(p, 'wb').write(t3.encode('utf-8'))

# ============ D) 海军变体 ============
print()
print('=' * 60)
print('【D】海军变体修复')

def edit_file(p, edits, tag):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    for old, new in edits:
        n = t.count(old)
        if n == 0:
            print(f'    {tag}: ★未找到: {old[:70]}')
            continue
        t = t.replace(old, new)
        print(f'    {tag}: 替换×{n}: {old[:60]} → {new[:60]}')
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_{os.path.basename(p)}'))
        open(p, 'wb').write(t.encode('utf-8'))

for tag, (base, _) in BASE_TXT.items():
    # D1 INA cru_2 变体重命名 + 2 舰同步
    p = os.path.join(base, 'history', 'countries', 'INA - Inazuma.txt')
    edits = [('name = "Sumeru_Class"\r\n\t\ttype = ship_hull_cruiser_2',
              'name = "Sumeru_Cruiser_2_Class"\r\n\t\ttype = ship_hull_cruiser_2')]
    # 若 CRLF 不匹配再试 LF 版
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    if 'name = "Sumeru_Class"\r\n' not in t:
        edits = [('name = "Sumeru_Class"\n\t\ttype = ship_hull_cruiser_2',
                  'name = "Sumeru_Cruiser_2_Class"\n\t\ttype = ship_hull_cruiser_2')]
    edit_file(p, edits, tag)
    # 同步舰
    up = os.path.join(base, 'history', 'units', 'INA_1936_naval.txt')
    if not os.path.exists(up):
        up = os.path.join(base, 'history', 'units', 'INA_1936_Naval.txt')
    t2 = open(up, encoding='utf-8-sig', errors='replace').read()
    n = t2.count('ship_hull_cruiser_2 = { amount = 1 owner = INA version_name = "Sumeru_Class" }')
    t2b = t2.replace('ship_hull_cruiser_2 = { amount = 1 owner = INA version_name = "Sumeru_Class" }',
                     'ship_hull_cruiser_2 = { amount = 1 owner = INA version_name = "Sumeru_Cruiser_2_Class" }')
    print(f'    {tag}: INA 舰 cruiser_2 引用更新 ×{n}')
    if APPLY:
        shutil.copy2(up, os.path.join(BD, f'{tag}_INA_naval.txt'))
        open(up, 'wb').write(t2b.encode('utf-8'))

    # D2 FAV heavy_2 去 front_1_custom_slot
    p = os.path.join(base, 'history', 'countries', 'FAV - Favonius.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    t2 = re.sub(r'(?m)^\s*front_1_custom_slot\s*=\s*\S+\s*\r?\n', '', t)
    n = len(re.findall(r'(?m)^\s*front_1_custom_slot', t))
    print(f'    {tag}: FAV front_1_custom_slot 删除 ×{n}')
    if APPLY and n:
        shutil.copy2(p, os.path.join(BD, f'{tag}_FAV.txt'))
        open(p, 'wb').write(t2.encode('utf-8'))
    # 完整性
    t3 = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'    {tag}: FAV 文件 {{={t3.count("{")} }}={t3.count("}")} (平衡={t3.count("{")-t3.count("}")})')

# ============ E) 只读报告 ============
print()
print('=' * 60)
print('【E1】41 个海洋州 manpower（用户问：是否不为 0）')
vals = collections.Counter()
for s in g_sea:
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{s}*.txt'))
          if re.match(rf'^{s}(\(|-)', os.path.basename(f))]
    if fs:
        t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'(?m)^\s*manpower\s*=\s*(\d+)', t)
        v = m.group(1) if m else '无字段'
        vals[v] += 1
print(f'  manpower 值分布: {dict(vals)}')

print()
print('【E2】INA + FAV 全部舰船的 version_name')
for base, fn in ((G, 'INA_1936_naval.txt'), (G, 'FAV_1936_naval.txt')):
    p = os.path.join(base, 'history', 'units', fn)
    if not os.path.exists(p):
        continue
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'  --- {fn} ---')
    for m in re.finditer(r'ship = \{ name = "([^"]+)"[^\n]*', t):
        l = m.group(0)
        hull = re.search(r'(ship_hull_\w+)', l)
        vn = re.search(r'version_name\s*=\s*"([^"]*)"', l)
        print(f'    {m.group(1):22s} hull={hull.group(1) if hull else "?":22s} version_name={vn.group(1) if vn else "★无"}')

print()
print('【E3】全 units 目录中引用 4 个变体名的其他文件（重命名安全检查）')
for name in ('Sumeru_Class', 'Snezhnaya_Class', 'Mondstadt_Class', 'Fontaine_Class'):
    hits = []
    for f in glob.glob(os.path.join(G, 'history', 'units', '*')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        n = t.count(name)
        if n:
            hits.append((os.path.basename(f), n))
    print(f'  {name}: {hits}')

print()
print(f'模式: {"已应用(APPLY)" if APPLY else "DRY（加 --apply）"}  备份目录: {BD}')

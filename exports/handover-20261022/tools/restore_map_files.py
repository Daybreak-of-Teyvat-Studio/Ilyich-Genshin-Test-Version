# -*- coding: utf-8 -*-
"""restore_map_files.py —— 地图文件修复包
1) buildings.txt 两行坏行（317 坐标落到 283）→ 挪进 317 自己的省内部
2) airports.txt 重建：beta 740 行站点 → gamma 750 州（省 id 直接沿用，州号按坐标/归属重算）
3) rocketsites.txt 同法重建
4) supply_nodes.txt 从 beta 185 行恢复（dead id 剔除）
5) railways.txt 从 beta 370 行恢复（dead 节点剔除、州号重算）
6) 8 座宫殿恢复（坐标→gamma 州）
先 DRY 输出统计，再写入（仓库+副本双写，先备份）。
"""
import os, re, sys, glob, struct, collections, datetime, shutil

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
COPIES = [('仓库', G),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'maprestore_{stamp}')
os.makedirs(BD, exist_ok=True)

APPLY = '--apply' in sys.argv

# ================= 基础数据 =================
def load_def(base):
    kinds, colors = {}, {}
    for l in open(os.path.join(base, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
        c = l.strip().split(';')
        if len(c) >= 5:
            try:
                pid = int(c[0])
            except ValueError:
                continue
            kinds[pid] = c[4]
            colors[(int(c[1]), int(c[2]), int(c[3]))] = pid
    return kinds, colors

gk, gcolors = load_def(G)
bk, bcolors = load_def(B)
print(f'gamma 省 {len(gk)} / beta 省 {len(bk)}')

def load_states(base, kind_map):
    """返 (state -> [prov...]), (prov -> state)"""
    s2p, p2s = {}, {}
    for f in glob.glob(os.path.join(base, 'history', 'states', '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'id\s*=\s*(\d+)', t)
        m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        if not (m and m2):
            continue
        sid = int(m.group(1))
        provs = [int(x) for x in re.findall(r'\d+', m2.group(1))]
        s2p[sid] = provs
        for p in provs:
            p2s.setdefault(p, sid)
    return s2p, p2s

g_s2p, g_p2s = load_states(G, gk)
b_s2p, b_p2s = load_states(B, bk)
print(f'gamma 州 {len(g_s2p)} / beta 州 {len(b_s2p)}')

# gamma 州 → 陆地省列表
g_land_of = {s: [p for p in provs if gk.get(p) == 'land'] for s, provs in g_s2p.items()}
# gamma 海洋州
g_sea_states = sorted(s for s, provs in g_s2p.items()
                      if provs and all(gk.get(p) == 'sea' for p in provs))
# gamma 沿海陆地省
g_coastal_land = [p for p, k in gk.items() if k == 'land']

# bmp（用于 fallback 找邻陆）
raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
W, H = struct.unpack('<ii', raw[18:26])
RB = W * 3
PIX = raw[off:]

def px(x, z):
    i = z * RB + x * 3
    return gcolors.get((PIX[i + 2], PIX[i + 1], PIX[i]))

# ================= 1) buildings 两行坏行 =================
print()
print('=' * 60)
print('【1】buildings.txt 317 两行坏行')
FIX_ROWS = [
    ('317;special_project_facility_spawn;1796.00;11.91;1396.00;2.45;0',
     '317;special_project_facility_spawn;1798.00;11.91;1394.00;2.45;0', 2969),
    ('317;industrial_complex;1824.00;11.70;1409.00;4.19;0',
     '317;industrial_complex;1826.00;11.70;1408.00;4.19;0', 2957),
]

def apply_bld(base, tag):
    p = os.path.join(base, 'map', 'buildings.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    nfix = 0
    for old, new, expect_prov in FIX_ROWS:
        n = t.count(old)
        assert n == 1, f'{tag}: 坏行匹配 {n} 次(应1): {old[:60]}'
        # 验证新坐标确实落在目标省
        c = new.split(';')
        x, z = int(float(c[2])), int(float(c[4]))
        got = px(x, z)
        assert got == expect_prov, f'{tag}: 新坐标落省 {got} != {expect_prov}'
        t = t.replace(old, new)
        nfix += 1
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_buildings.txt'))
        open(p, 'wb').write(t.encode('utf-8'))
    print(f'  {tag}: 修复 {nfix} 行 ✓')

for tag, base in COPIES:
    apply_bld(base, tag)

# ================= 2/3) airports + rocketsites =================
def build_site_file(beta_file, out_name):
    """beta 站点表 → gamma 750 州站点表"""
    t = open(os.path.join(B, 'map', beta_file), encoding='utf-8-sig', errors='replace').read()
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    cand = collections.defaultdict(list)   # gamma_state -> [prov]
    dead = 0
    for l in lines:
        m = re.match(r'(\d+)\s*=\s*\{([^}]*)\}', l)
        if not m:
            continue
        for ps in re.findall(r'\d+', m.group(2)):
            p = int(ps)
            if p in gk and gk[p] == 'land' and p in g_p2s:
                gs = g_p2s[p]
                if p not in cand[gs]:
                    cand[gs].append(p)
            else:
                dead += 1
    # 补全：没有站点的州
    fallback = 0
    out = {}
    for s in range(1, 751):
        if s in cand:
            out[s] = cand[s]
            continue
        if g_land_of.get(s):
            out[s] = [g_land_of[s][0]]
            fallback += 1
        else:
            # 海洋州：beta 海洋州配对由调用方补充（这里先用占位 None）
            out[s] = None
    print(f'  {out_name}: 收集候选州 {len(cand)}，dead 站点 {dead}，陆地 fallback {fallback}，'
          f'海洋州待配 {sum(1 for v in out.values() if v is None)}')
    return out

air = build_site_file('airports.txt', 'airports.txt')
roc = build_site_file('rocketsites.txt', 'rocketsites.txt')

# ---- 海洋州配对：beta 海洋州 ↔ gamma 海洋州（省重合度）----
b_sea_states = sorted(s for s, provs in b_s2p.items()
                      if provs and all(bk.get(p) == 'sea' for p in provs))
print(f'  beta 海洋州 {len(b_sea_states)} 个: {b_sea_states[:8]}... gamma 海洋州 {len(g_sea_states)} 个')

# beta 站点（海洋州部分）：从 beta 文件取
def beta_sea_sites(beta_file):
    t = open(os.path.join(B, 'map', beta_file), encoding='utf-8-sig', errors='replace').read()
    d = {}
    for l in t.split('\n'):
        m = re.match(r'(\d+)\s*=\s*\{([^}]*)\}', l.strip())
        if m:
            sid = int(m.group(1))
            ps = [int(x) for x in re.findall(r'\d+', m.group(2))]
            d[sid] = ps
    return d

for fname, table in (('airports.txt', air), ('rocketsites.txt', roc)):
    bs = beta_sea_sites(fname)
    # 配对
    pairs = {}
    used = set()
    for gs in g_sea_states:
        gprovs = set(g_s2p[gs])
        best, bestov = None, 0
        for bs2 in b_sea_states:
            if bs2 in used:
                continue
            ov = len(gprovs & set(b_s2p[bs2]))
            if ov > bestov:
                best, bestov = bs2, ov
        if best is not None and bestov > 0:
            pairs[gs] = best
            used.add(best)
    print(f'  {fname}: 海洋州配对 {len(pairs)}/{len(g_sea_states)}')
    # 赋站点 + fallback（邻陆表单次全图扫描构建）
    if 'SEA_NB' not in globals():
        SEA_NB = {}
        sea_prov2state = {p: s for s, provs in g_s2p.items() for p in provs if gk.get(p) == 'sea'}
        for z in range(1, H - 1, 2):
            for x in range(1, W - 1, 2):
                q = gcolors.get((PIX[z * RB + x * 3 + 2], PIX[z * RB + x * 3 + 1], PIX[z * RB + x * 3]))
                if q is None or gk.get(q) != 'land':
                    continue
                # 检查四邻是否有海省，把海省→该陆省记下
                for dx, dz in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                    r = gcolors.get((PIX[(z + dz) * RB + (x + dx) * 3 + 2],
                                     PIX[(z + dz) * RB + (x + dx) * 3 + 1],
                                     PIX[(z + dz) * RB + (x + dx) * 3]))
                    if r is not None and gk.get(r) == 'sea':
                        ss = sea_prov2state.get(r)
                        if ss is not None and ss not in SEA_NB:
                            SEA_NB[ss] = q
        globals()['SEA_NB'] = SEA_NB
        print(f'    邻陆表: {len(SEA_NB)}/{len(g_sea_states)} 海洋州')
    n_beta, n_nb = 0, 0
    for gs in g_sea_states:
        bsite = None
        if gs in pairs:
            for p in bs.get(pairs[gs], []):
                if p in gk and gk[p] == 'land':
                    bsite = p
                    break
        if bsite:
            table[gs] = [bsite]
            n_beta += 1
        else:
            found = SEA_NB.get(gs)
            table[gs] = [found] if found else [g_coastal_land[0]]
            n_nb += 1
    print(f'    beta 站点沿用 {n_beta}，邻陆 fallback {n_nb}')
    miss = [s for s, v in table.items() if not v]
    assert not miss, f'仍有空州: {miss}'

# ---- 写出 ----
def write_site_file(table, fname):
    lines = []
    for s in range(1, 751):
        ps = table[s]
        body = ' '.join(str(p) for p in ps)
        lines.append(f'{s}={{{body} }}')
    return ('\r\n'.join(lines) + '\r\n')

for fname in ('airports.txt', 'rocketsites.txt'):
    table = air if fname == 'airports.txt' else roc
    content = write_site_file(table, fname)
    for tag, base in COPIES:
        p = os.path.join(base, 'map', fname)
        if APPLY:
            if os.path.exists(p):
                shutil.copy2(p, os.path.join(BD, f'{tag}_{fname}'))
            open(p, 'wb').write(content.encode('utf-8'))
    print(f'  写出 {fname}: {len(content.splitlines())} 行')

# ================= 4) supply_nodes =================
print()
print('=' * 60)
print('【4】supply_nodes.txt')
t = open(os.path.join(B, 'map', 'supply_nodes.txt'), encoding='utf-8-sig', errors='replace').read()
sites, dead = [], []
for l in t.split('\n'):
    if not l.strip():
        continue
    c = l.split()
    if len(c) >= 2:
        p = int(c[1])
        (sites if (p in gk and gk[p] == 'land') else dead).append(p)
content = ''.join(f'1 {p} \r\n' for p in sites)
for tag, base in COPIES:
    p = os.path.join(base, 'map', 'supply_nodes.txt')
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_supply_nodes.txt'))
        open(p, 'wb').write(content.encode('utf-8'))
print(f'  恢复 {len(sites)} 行，剔除 dead {len(dead)}')

# ================= 5) railways（默认跳过：空文件已被引擎容忍，恢复需邻接校验）
print()
print('=' * 60)
print('【5】railways.txt —— 默认跳过（需按新地图做邻接校验，另行处理）')
if '--railways' in sys.argv:
    t = open(os.path.join(B, 'map', 'railways.txt'), encoding='utf-8-sig', errors='replace').read()
    out_lines, node_dead, dropped = [], 0, 0
    for l in t.split('\n'):
        c = l.split()
        if len(c) < 3:
            continue
        try:
            n = int(c[1])
            nodes = [int(x) for x in c[2:2 + n]]
        except ValueError:
            continue
        keep = []
        for p in nodes:
            if p in gk and gk[p] == 'land' and p in g_p2s:
                keep.append(p)
            else:
                node_dead += 1
        if len(keep) >= 2:
            st = g_p2s[keep[0]]
            out_lines.append(f'{st} {len(keep)} ' + ' '.join(str(x) for x in keep))
        else:
            dropped += 1
    content = '\r\n'.join(out_lines) + '\r\n'
    for tag, base in COPIES:
        p = os.path.join(base, 'map', 'railways.txt')
        if APPLY:
            shutil.copy2(p, os.path.join(BD, f'{tag}_railways.txt'))
            open(p, 'wb').write(content.encode('utf-8'))
    print(f'  恢复 {len(out_lines)} 条铁路，剔除 dead 节点 {node_dead}，丢弃过短 {dropped}')

# ================= 6) 宫殿 =================
print()
print('=' * 60)
print('【6】宫殿')
# 检查类型是否存在于 gamma 定义
types_ok = {}
common_b = os.path.join(G, 'common', 'buildings')
pal_types = ['MOT_Palace', 'LYY_Palace', 'INA_Palace', 'SUM_Palace',
             'FON_Palace', 'NAT_Palace', 'NDK_Palace', 'SNE_Palace']
txt = ''
for f in glob.glob(os.path.join(common_b, '*.txt')):
    txt += open(f, encoding='utf-8-sig', errors='replace').read()
for p in pal_types:
    types_ok[p] = (p in txt)
print('  类型存在性:', types_ok)

pal_lines = []
for l in open(os.path.join(B, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if 'Palace' in l and ';' in l:
        c = l.strip().split(';')
        if len(c) >= 7 and c[1].strip() in pal_types:
            x, z = int(float(c[2])), int(float(c[4]))
            prov = px(x, z)
            if prov is None or gk.get(prov) != 'land':
                # 邻域找陆地
                for r in range(1, 30):
                    done = False
                    for dx in range(-r, r + 1):
                        for dz in range(-r, r + 1):
                            if max(abs(dx), abs(dz)) != r:
                                continue
                            q = px(x + dx, z + dz)
                            if q is not None and gk.get(q) == 'land':
                                prov, done = q, True
                                break
                        if done:
                            break
                    if done:
                        break
            if prov and prov in g_p2s:
                st = g_p2s[prov]
                pal_lines.append(f'{st};{c[1].strip()};{c[2]};{c[3]};{c[4]};{c[5]};0')
            else:
                print(f'  ★ {c[1].strip()} 坐标无解: {l.strip()}')
for l in pal_lines:
    print('   ', l)

if all(types_ok.values()) and pal_lines and '--palaces' in sys.argv:
    for tag, base in COPIES:
        p = os.path.join(base, 'map', 'buildings.txt')
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        if 'Palace' not in t:
            t = t.rstrip('\r\n') + '\r\n' + '\r\n'.join(pal_lines) + '\r\n'
            if APPLY:
                open(p, 'wb').write(t.encode('utf-8'))
            print(f'  {tag}: 追加 {len(pal_lines)} 行宫殿 ✓')
        else:
            print(f'  {tag}: 已含 Palace，跳过')
else:
    print('  ★ 宫殿跳过：beta 坐标在 gamma 地图上失效（全落海），需按新地图重新定点（--palaces 强制）')

# ================= 验证 =================
if APPLY:
    print()
    print('=' * 60)
    print('【验证】回读仓库文件')
    for tag, base in COPIES:
        ok = []
        for fname in ('airports.txt', 'rocketsites.txt', 'supply_nodes.txt'):
            p = os.path.join(base, 'map', fname)
            t = open(p, encoding='utf-8-sig', errors='replace').read()
            lines = [l for l in t.split('\n') if l.strip()]
            if fname == 'supply_nodes.txt':
                good = all(int(l.split()[1]) in gk for l in lines if len(l.split()) >= 2)
                ok.append(f'{fname}={len(lines)}行/{ "全合法" if good else "★有非法" }')
            else:
                n_state, bad_site = 0, 0
                for l in lines:
                    m = re.match(r'(\d+)\s*=\s*\{([^}]*)\}', l)
                    if not m:
                        bad_site += 1
                        continue
                    n_state += 1
                    for ps in re.findall(r'\d+', m.group(2)):
                        if gk.get(int(ps)) != 'land':
                            bad_site += 1
                ok.append(f'{fname}={n_state}州/非法站点{bad_site}')
        # buildings 两行
        p = os.path.join(base, 'map', 'buildings.txt')
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        fixed = all(new in t for _, new, _ in FIX_ROWS)
        ok.append(f'buildings317修复={fixed}')
        print(f'  {tag}: ' + ' | '.join(ok))

print()
print(f'模式: {"已应用(APPLY)" if APPLY else "DRY（加 --apply 应用）"}')
print(f'备份目录: {BD}')

# -*- coding: utf-8 -*-
"""verify_mapfix2.py —— 修复后最终验证（双副本）"""
import os, re, sys, glob, struct

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

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

s2p = {}
p2s = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        sid = int(m.group(1))
        s2p[sid] = [int(x) for x in re.findall(r'\d+', m2.group(1))]
        for p in s2p[sid]:
            p2s.setdefault(p, sid)
g_sea = sorted(s for s, provs in s2p.items() if provs and all(gk.get(p) == 'sea' for p in provs))

FIXED_LINES = [1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 3192,
               8009, 8013, 15210, 15217, 15230, 15233, 16006, 16100, 16662, 16749, 17028, 17031, 17036,
               17052, 17157, 17512, 17513, 17528, 17534, 17637, 17680, 17774, 17778, 18005, 18071, 18084,
               18099, 18173, 18414, 18509, 18546, 18555, 18588, 18630, 18647, 18771, 18772, 18773, 18775,
               18777, 18788, 18918, 18939, 19109, 19126, 19137, 19672, 19673, 20206, 20377, 20398, 20406,
               20879, 20880, 20887, 20904, 24800, 24802, 25977, 25984, 26304, 26645, 28720, 29804, 31945,
               32930, 33548, 33935, 34283, 35273, 35675, 35855, 35980, 36066, 37005, 37968, 38134, 38476,
               38541, 38672, 38762, 38806, 38807, 38808, 38884, 38920, 38921, 38963, 39064, 39106, 39140,
               39191, 39226, 39256, 39273, 39294, 39399, 39415, 39691, 39749, 39751, 39769, 39771, 39772,
               39891, 40073, 40132, 40133, 40552, 40584, 40585]

for tag, base in COPIES:
    print('=' * 66)
    print(f'【{tag}】')
    p = os.path.join(base, 'map', 'buildings.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    lines = t.split('\n')
    ls = [l for l in lines if l.strip()]
    blanks = len(lines) - len(ls)
    print(f'  行数 {len(ls)} (含尾空 {blanks})')
    # 120 修复行的坐标验证
    ok, bad = 0, []
    for ln in FIXED_LINES:
        row = ls[ln - 1]
        c = row.split(';')
        st = int(c[0])
        prov = px(int(float(c[2])), int(float(c[4])))
        if prov is not None and p2s.get(prov) == st and gk.get(prov) == 'land':
            ok += 1
        else:
            bad.append((ln, st, prov, p2s.get(prov)))
    print(f'  120 修复行坐标验证: {ok}/120 通过' + (f' ★失败: {bad[:5]}' if bad else ''))
    # 海州行
    nsea = sum(1 for l in ls if l.split(';')[0].isdigit() and int(l.split(';')[0]) in g_sea)
    print(f'  海州新增行: {nsea} (期望 328)')
    # 全图 land-cross 扫描（快速版：只查行非空且齐全）
    landcross = 0
    for l in ls:
        c = l.split(';')
        if len(c) < 7:
            continue
        try:
            st = int(c[0])
            prov = px(int(float(c[2])), int(float(c[4])))
        except ValueError:
            continue
        if prov is None:
            continue
        s = p2s.get(prov)
        if s is not None and s != st and gk.get(prov) == 'land':
            if st not in g_sea:  # 海州行预期在外州陆地，跳过
                landcross += 1
    print(f'  非海州陆地跨州行: {landcross} (期望 0)')
    # 海军
    p2 = os.path.join(base, 'history', 'countries', 'INA - Inazuma.txt')
    t2 = open(p2, encoding='utf-8-sig', errors='replace').read()
    print(f'  INA: Sumeru_Cruiser_2_Class ×{t2.count("Sumeru_Cruiser_2_Class")}, 旧重名对 ×{t2.count(chr(34)+"Sumeru_Class"+chr(34))}')
    up = os.path.join(base, 'history', 'units', 'INA_1936_naval.txt')
    if os.path.exists(up):
        t3 = open(up, encoding='utf-8-sig', errors='replace').read()
        print(f'  INA 舰: Sumeru_Cruiser_2_Class 引用 ×{t3.count("Sumeru_Cruiser_2_Class")}')
    p3 = os.path.join(base, 'history', 'countries', 'FAV - Favonius.txt')
    t4 = open(p3, encoding='utf-8-sig', errors='replace').read()
    print(f'  FAV: front_1_custom_slot ×{len(re.findall(r"(?m)^\s*front_1_custom_slot", t4))}')

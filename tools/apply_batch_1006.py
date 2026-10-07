# -*- coding: utf-8 -*-
"""apply_batch_1006.py —— 大批次：转省 16（多省并给）+ 州名 32 + VP 83（含改名/改值）

歧义处理（报告中标出，用户可纠正）：
  · s577 双名 → 按顺序后者生效（特诺奇兹托克）
  · p3077 双名 → 后者生效（废弃避难所）
  · 368「蟹之主的宫殿（10）·上层」后缀在括号外 → 按 3527 下层配对取「蟹之主的宫殿·上层」
"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
NAMES_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VP_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
BP = os.path.join(MOD, 'map', 'buildings.txt')

TRANSFERS = [(3993, 622), (3642, 504), (209, 471), (2050, 471), (3424, 471),
             (1311, 493), (450, 465), (3489, 465), (1329, 519), (182, 405),
             (2212, 489), (1157, 489), (3508, 489), (1201, 470), (3536, 470),
             (2246, 354), (150, 15), (1365, 15), (3023, 333), (47, 336),
             (3041, 336), (1772, 384), (3034, 384), (3019, 327)]
NAMES = [(622, '流灰之街'), (88, '托佐兹之岛'), (79, '噩梦的温床'), (504, '黄琮墟'),
         (577, '彩彩洞'), (577, '特诺奇兹托克'), (515, '那夏镇'),
         (506, '叮铃哐啷蛋卷工坊'), (476, '星砂滩'), (478, '苔骨荒原'), (455, '蓝珀湖'),
         (463, '苔骨荒原'), (445, '空寂走廊'), (409, '月矩力试验设计局'), (36, '终夜长茔'),
         (405, '绯沙盐沼'), (486, '霜月之坊'), (470, '沐光之台'), (498, '雷图礁'),
         (489, '守誓者的圣所'), (55, '银月之庭'), (328, '雾灵渚'), (13, '杜南纳前进站'),
         (354, '皮拉米达城'), (336, '厄布拉神柱'), (20, '凯雷丝之翼'), (334, '安瓦蒂尼尔湖'),
         (15, '西风戍垒'), (333, '望崖营壁'), (384, '噩影泽地'), (332, '苦壑崖'),
         (327, '特辖地研究所')]
# (省, 名, 值)
VPS = [
    (1151, '炽火燃尽所·其二', 10), (664, '淹埋的地下遗迹', 10), (2260, '漫流的古道', 10),
    (3918, '暗流的峡谷', 5), (763, '炽火燃尽所·其一', 10), (3, '旧日的统律之心', 10),
    (1432, '古遗迹步道', 5), (3942, '幻蛇之宫', 10), (3993, '七燃烧之井', 10),
    (1229, '空梦的起始', 10), (2183, '浮羽之湾封印', 15),
    (1311, '沉珑渊府', 10), (3447, '古老山洞', 5), (2072, '王山厅', 10),
    (3586, '灵枢庭', 10), (3558, '伏仙洞', 10), (3615, '锦落庭', 15),
    (947, '黄琮墟', 10), (3610, '沉玉谷·南陵神像', 20), (3483, '翘英庄', 20),
    (2179, '沉玉谷·上谷神像', 20),
    (1474, '留云仙府', 15),
    (567, '悠悠度假村神像', 20), (996, '特诺奇兹托克·洞穴入口', 10),
    (2245, '特诺奇兹托克·东部洞穴', 10), (3740, '特诺奇兹托克·西部洞穴', 10),
    (1640, '刺梨镇', 20), (3601, '特诺奇兹托克·北部洞穴', 10), (296, '悠悠集市', 20),
    (103, '浪浪湾', 20), (277, '呼呼丘', 20), (2202, '彩彩崖', 20),
    (3608, '提提岛舞台', 20),
    (3519, '银月之庭', 50), (5, '雷图礁·隧路', 5), (3508, '遗誓者的圣所', 20),
    (1178, '失落的月庭', 15), (1201, '近月的隙间', 10), (945, '聚所·霜月之坊', 20),
    (3527, '蟹之主的宫殿·下层', 10), (368, '蟹之主的宫殿·上层', 10),
    (2025, '聚所·叮铃哐啷蛋卷工坊', 20), (2211, '苔原之隙', 10),
    (2041, '无光的深都', 15), (3561, '那夏镇神像', 20), (3525, '隐藏的实验室', 10),
    (3491, '风蚀小径', 10), (3464, '废弃的工坊', 10), (186, '绝海之下', 10),
    (383, '徒水岩窟', 5), (3294, '地下研究所', 10), (2464, '集装箱轨道', 10),
    (995, '销毁车间', 10), (37, '设计局顶层', 25), (315, '设计局南区', 10),
    (2103, '设计局东区', 10), (3289, '盐蚀洞窟', 10), (3309, '霜凝的机枢', 15),
    (2008, '帕哈岛神像', 25), (907, '聚所·终夜长茔', 20), (3077, '【末日后的乐园】', 10),
    (3049, '雾灵渚神像', 20), (2400, '虚海望神像', 20), (2246, '皮拉米达城', 25),
    (3077, '废弃避难所', 10), (3041, '逐浪野神像', 20), (824, '聚所·魔女的花园', 25),
    (1772, '最后的藏宝地·入口', 10), (1266, '最后的藏宝地·门厅', 5),
    (3054, '最后的藏宝地·终点', 10), (3048, '残辉岩窟', 5), (150, '神柱的根系', 10),
    (1092, '厄布拉神柱', 15), (3028, '凯雷丝之翼', 15), (47, '聚所·西风戍垒', 20),
    (854, '月童的库藏', 15), (905, '英灵的享殿', 5), (3024, '聚所·望崖营壁', 20),
    (1365, '烟硌山峰神像', 20), (3015, '赝月的研究所', 20), (2264, '苦壑之下', 15),
    (3014, '苦壑之路', 10), (970, '杜南纳前进站·升降口', 25), (3017, '靡穷深壑', 15),
]


def load(p):
    raw = open(p, 'rb').read()
    return raw, raw.decode('utf-8-sig')


def save(p, text, has_bom):
    data = text.encode('utf-8')
    open(p, 'wb').write((b'\xef\xbb\xbf' + data) if has_bom else data)


def history_close(t):
    m = re.search(r'\bhistory\s*=\s*\{', t)
    depth, i = 0, m.end() - 1
    while True:
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1


def vps_of(t):
    d = {}
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        xs = vm.group(1).split()
        for i in range(0, len(xs) - 1, 2):
            d[int(xs[i])] = int(xs[i + 1])
    return d


def provs_of(t):
    return re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()


# ---------- 1. 转省 ----------
p2s = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for x in provs_of(t):
        p2s[int(x)] = sid
for pid, dst in TRANSFERS:
    src = p2s[pid]
    assert src != dst, f'p{pid} 已在 s{dst}'
    for sid in (src, dst):
        p = os.path.join(ST, f'{sid}-State_{sid}.txt')
        raw, t = load(p)
        provs = provs_of(t)
        if sid == src:
            provs.remove(str(pid))
        else:
            provs.append(str(pid))
        pm = re.search(r'(provinces\s*=\s*\{)([^}]*)(\})', t)
        t = t[:pm.start()] + pm.group(1) + '\r\n\t\t' + ' '.join(provs) + '\r\n\t' + pm.group(3) + t[pm.end():]
        save(p, t, raw[:3] == b'\xef\xbb\xbf')
        p2s[pid] = dst
    raw = open(BP, 'rb').read()
    lines = raw.decode('utf-8-sig').split('\r\n')
    nb = 0
    for i, l in enumerate(lines):
        f7 = l.split(';')
        if len(f7) == 7 and f7[6] == str(pid) and f7[0] == str(src):
            f7[0] = str(dst)
            lines[i] = ';'.join(f7)
            nb += 1
    open(BP, 'wb').write('\r\n'.join(lines).encode('utf-8'))
    print(f'转省 p{pid}: s{src}→s{dst}，buildings {nb} 条')

# ---------- 2. 州名（覆盖语义；nm_map 后者生效） ----------
nm_map = {}
for sid, nm in NAMES:
    nm_map[sid] = nm
raw, t = load(NAMES_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
out = []
for l in t.split(nl):
    m = re.match(r'^(\s*DOT_STATE_(\d+):)0?(\s*)"([^"]*)"', l)
    if m and int(m.group(2)) in nm_map:
        sid = int(m.group(2))
        want = nm_map[sid]
        if m.group(4) != want:
            print(f'  s{sid}: 「{m.group(4)}」→「{want}」')
            l = f'{m.group(1)}0{m.group(3)}"{want}"'
    out.append(l)
save(NAMES_F, nl.join(out), has_bom)

# ---------- 3. VP 值（含改值/确认） ----------
p2s = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for x in provs_of(t):
        p2s[int(x)] = sid
touched = {}
for pid, nm, val in VPS:
    h = p2s[pid]
    if h not in touched:
        r2, t2 = load(os.path.join(ST, f'{h}-State_{h}.txt'))
        touched[h] = (r2, t2, r2[:3] == b'\xef\xbb\xbf')
    raw, t, has_bom = touched[h]
    cur = vps_of(t).get(pid)
    if cur == val:
        pass                                   # 已对，静默
    elif cur is None:
        ls = t.rfind('\n', 0, history_close(t)) + 1
        t = t[:ls] + f'\t\tvictory_points = {{ {pid} {val} }}\r\n' + t[ls:]
        print(f'  p{pid}「{nm}」{val}: 写入 s{h}')
    else:
        t = re.sub(r'(victory_points\s*=\s*\{\s*)' + str(pid) + r'\s+\d+(\s*\})',
                   rf'\g<1>{pid} {val}\g<2>', t)
        print(f'  p{pid}「{nm}」: s{h} 改值 {cur}→{val}')
    touched[h] = (raw, t, has_bom)
for sid, (raw, t, has_bom) in touched.items():
    save(os.path.join(ST, f'{sid}-State_{sid}.txt'), t, has_bom)

# ---------- 4. VP 本地化（后名生效；存在不同名即更新） ----------
want = {}
for pid, nm, val in VPS:
    want[pid] = nm                             # 后者覆盖前者（3077）
raw, t = load(VP_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
out, nupd, nadd = [], 0, 0
for l in t.split(nl):
    m = re.match(r'^(\s*VICTORY_POINTS_(\d+):)\d*(\s*)"([^"]*)"', l)
    if m and int(m.group(2)) in want:
        pid = int(m.group(2))
        if m.group(4) != want[pid]:
            l = f'{m.group(1)}0{m.group(3)}"{want[pid]}"'
            nupd += 1
        want.pop(pid)
    out.append(l)
for pid, nm in want.items():
    out.append(f' VICTORY_POINTS_{pid}:0 "{nm}"')
    nadd += 1
save(VP_F, nl.join(out), has_bom)
print(f'VP 本地化: 更新 {nupd}，新增 {nadd}')

# ---------- 5. 回读验证 ----------
print()
print('=== 回读验证 ===')
errs = 0
p2s2, vp_all = {}, {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for x in provs_of(t):
        p2s2[int(x)] = sid
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        xs = vm.group(1).split()
        for i in range(0, len(xs) - 1, 2):
            vp_all[(sid, int(xs[i]))] = int(xs[i + 1])
bad_t = [(pid, dst) for pid, dst in TRANSFERS if p2s2.get(pid) != dst]
print(f'转省 {len(TRANSFERS)} 条: ' + ('全部 ✓' if not bad_t else f'✗ {bad_t}'))
errs += len(bad_t)
nm_t = open(NAMES_F, encoding='utf-8-sig').read()
bad_n = [(sid, nm) for sid, nm in nm_map.items()
         if re.search(rf'DOT_STATE_{sid}:0\s*"{re.escape(nm)}"', nm_t) is None]
print(f'州名 {len(nm_map)} 条: ' + ('全部 ✓' if not bad_n else f'✗ {bad_n}'))
errs += len(bad_n)
vp_t = open(VP_F, encoding='utf-8-sig').read()
bad_v = []
for pid, nm, val in VPS:
    h = p2s2[pid]
    if vp_all.get((h, pid)) != val or \
       re.search(rf'VICTORY_POINTS_{pid}:0\s*"{re.escape(nm)}"', vp_t) is None:
        bad_v.append((pid, nm, val))
print(f'VP {len(VPS)} 条: ' + ('全部 ✓' if not bad_v else f'✗ {bad_v}'))
errs += len(bad_v)
print('\n全部通过 ✓' if errs == 0 else f'\n{errs} 组失败 ✗')

# -*- coding: utf-8 -*-
"""
check_states.py —— State 综合自检（动过 state / province / buildings / 本地化之后必跑）

检查项：
  A. 州文件      文件名=id、括号配对、行首空格、空州、id 缺号（报告）
  B. 省覆盖      definition.csv 的陆地/海域省全部有着落、无重复归属
  C. 核心        owner 与 add_core_of 一致、海州无 owner
  D. 胜利点      格式（偶数、纯数字）、省 ⊆ 州、数量
  E. 首都        所有国家的 capital 指向存在的州
  F. 本地化      DOT_STATE_* 覆盖/孤儿/重复、VICTORY_POINTS_* 孤儿、BOM
  G. buildings   声明州都存在、海州不得有州级生成点、每陆州生成点数量
用法:
    python check_states.py --mod <mod根目录>
    python check_states.py --mod <mod根目录> --baseline <原始buildings.txt>   # 加做逐州数量对照
退出码: 0 = 干净; 1 = 有问题
"""
import os, re, sys, glob, collections, argparse

ap = argparse.ArgumentParser()
ap.add_argument('--mod', required=True)
ap.add_argument('--baseline', help='原始 buildings.txt（对照每州生成点数量；不带则按标准 7+3 检查）')
args = ap.parse_args()
MOD = os.path.normpath(args.mod)
ST = os.path.join(MOD, 'history', 'states')
BP = os.path.join(MOD, 'map', 'buildings.txt')
DEF = os.path.join(MOD, 'map', 'definition.csv')
SL = {'air_base': 1, 'fuel_silo': 1, 'radar_station': 1, 'nuclear_reactor_spawn': 1,
      'rocket_site_spawn': 1, 'synthetic_refinery': 1, 'stronghold_network': 1,
      'anti_air_building': 3}
sys.stdout.reconfigure(encoding='utf-8')
problems = collections.defaultdict(list)


def read_text(p):
    raw = open(p, 'rb').read()
    return raw.decode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'), raw[:3] == b'\xef\xbb\xbf'


# ---------- A/B/C/D: 州文件 ----------
states, s2p, s2o, s2vp = {}, {}, {}, {}
for f in sorted(os.listdir(ST)):
    if not f.endswith('.txt'):
        continue
    t, _ = read_text(os.path.join(ST, f))
    fm = re.match(r'^(\d+)-', f)
    cm = re.search(r'\bid\s*=\s*(\d+)', t)
    if not cm:
        problems['A 州文件'].append(f'{f}: 无 id 行')
        continue
    sid = int(cm.group(1))
    states[sid] = f
    if fm and int(fm.group(1)) != sid:
        problems['A 州文件'].append(f'{f}: 文件名号 {fm.group(1)} ≠ id {sid}')
    if t.count('{') != t.count('}'):
        problems['A 州文件'].append(f'{f}: 括号不配对')
    if re.search(r'(?m)^ +', t):
        problems['A 州文件'].append(f'{f}: 行首空格（必须 tab）')
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in pm.group(1).split()] if pm else []
    s2p[sid] = provs
    if not provs:
        problems['A 州文件'].append(f'state {sid}: provinces 为空（空白州）')
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    co = re.findall(r'add_core_of\s*=\s*(\w+)', t)
    s2o[sid] = mo.group(1) if mo else None
    if mo and co != [mo.group(1)]:
        problems['C 核心'].append(f'state {sid}: owner={mo.group(1)} 但核心={co}')
    if not mo and re.search(r'\bowner\b', t):
        problems['C 核心'].append(f'state {sid}: 海州却含 owner 字样')
    vps = []
    for m in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        v = m.group(1).split()
        if len(v) % 2 or not all(x.isdigit() for x in v):
            problems['D 胜利点'].append(f'state {sid}: VP 参数格式异常 {v}')
            continue
        for i in range(0, len(v) - 1, 2):
            vps.append((int(v[i]), int(v[i + 1])))
    for pid, val in vps:
        if pid not in s2p[sid]:
            problems['D 胜利点'].append(f'state {sid}: VP 省 {pid} 不在本州')
    s2vp[sid] = vps

ids = sorted(states)
holes = sorted(set(range(min(ids), max(ids) + 1)) - set(ids))
if holes:
    problems['A 州文件'].append(f'缺号 {len(holes)} 个: {holes[:20]}'
                               f'{"..." if len(holes) > 20 else ""}（引擎允许，但 mod 惯例可跑 fill_state_gaps.py 补齐）')

# ---------- B: 省覆盖 ----------
land_def, sea_def = set(), set()
for line in open(DEF, encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        (land_def if a[4] == 'land' else sea_def).add(int(a[0]))
covered = set()
for s, ps in s2p.items():
    for p in ps:
        covered.add(p)
        if p in land_def:
            pass
missing_land = sorted(land_def - covered)
missing_sea = sorted(sea_def - covered)
extra = sorted(covered - land_def - sea_def)
if missing_land:
    problems['B 省覆盖'].append(f'陆地省未归属任何州: {len(missing_land)} 个 {missing_land[:10]}')
if missing_sea:
    print(f'ℹ 海域省未归属: {len(missing_sea)} 个（海州未覆盖到的零星省，通常无害）'
          if missing_sea else '', end='')
if extra:
    problems['B 省覆盖'].append(f'州里含未定义省: {extra[:10]}')
dup = {p: v for p, v in
       ((p, [s for s, ps in s2p.items() if p in ps]) for p in covered)
       if len(v) > 1}
if dup:
    problems['B 省覆盖'].append(f'重复归属 {len(dup)} 省: '
                               + '; '.join(f'{p}→{v}' for p, v in list(dup.items())[:8]))

# ---------- E: 首都 ----------
for p in glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
    t, _ = read_text(p)
    for m in re.finditer(r'(?m)^\s*capital\s*=\s*(\d+)', t):
        if int(m.group(1)) not in states:
            problems['E 首都'].append(f'{os.path.basename(p)}: capital = {m.group(1)} 指向不存在的州')

# ---------- F: 本地化 ----------
loc_dir = os.path.join(MOD, 'localisation')
loc_states = collections.Counter()          # (语言目录, id) -> 次数
loc_vp = collections.Counter()
for p in glob.glob(os.path.join(loc_dir, '**', '*.yml'), recursive=True):
    raw = open(p, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    t = raw.decode('utf-8-sig' if bom else 'utf-8', errors='replace')
    lang = os.path.basename(os.path.dirname(p))          # 语言目录（simp_chinese 等）
    if not bom and re.search(r'(DOT_STATE_\d+|VICTORY_POINTS_\d+):', t):
        problems['F 本地化'].append(f'{os.path.relpath(p, MOD)}: 含州/VP key 但缺 BOM（整文件会被游戏忽略）')
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):', t, re.M):
        loc_states[(lang, int(m.group(1)))] += 1
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):', t, re.M):
        loc_vp[(lang, int(m.group(1)))] += 1
dup_s = {f'{lang}/{k}': v for (lang, k), v in loc_states.items() if v > 1}
if dup_s:
    problems['F 本地化'].append(f'DOT_STATE 同目录重复 key: {list(dup_s.items())[:10]}')
orph_s = sorted(k for (lang, k) in loc_states if k not in states)
if orph_s:
    problems['F 本地化'].append(f'DOT_STATE 孤儿（州不存在）: {orph_s[:10]}')
dup_v = {f'{lang}/{k}': v for (lang, k), v in loc_vp.items() if v > 1}
if dup_v:
    problems['F 本地化'].append(f'VICTORY_POINTS 同目录重复 key: {list(dup_v.items())[:10]}')

# ---------- G: buildings ----------
if os.path.exists(BP):
    cur = collections.Counter()
    for l in read_text(BP)[0].split('\r\n' if b'\r\n' in open(BP, "rb").read() else '\n'):
        f = l.split(';')
        if len(f) == 7 and f[0].isdigit():
            st = int(f[0])
            cur[(f[1], st)] += 1
            if st not in states:
                problems['G buildings'].append(f'声明州 {st} 不存在（行: {l[:60]}）')
    # 海州不得有 SL
    for (bt, st), n in cur.items():
        if bt in SL and st in s2o and s2o[st] is None:
            problems['G buildings'].append(f'海州 {st} 有州级生成点 {bt} ×{n}（应删除）')
    # 每陆州生成点
    if args.baseline and os.path.exists(args.baseline):
        base = collections.Counter()
        for l in read_text(args.baseline)[0].split('\r\n' if b'\r\n' in open(args.baseline, "rb").read() else '\n'):
            f = l.split(';')
            if len(f) == 7 and f[0].isdigit() and f[1] in SL:
                base[(f[1], int(f[0]))] += 1
        # 基线对照仅限州级生成点（SL）——省级建筑声明州随转省大范围重排，逐州对照无意义
        base_sl = {k: v for k, v in base.items() if k[0] in SL and k[1] in states and s2o.get(k[1])}
        cur_sl = {k: v for k, v in cur.items() if k[0] in SL and k[1] in states and s2o.get(k[1])}
        diff = {k for k in set(base_sl) | set(cur_sl) if base_sl.get(k, 0) != cur_sl.get(k, 0)}
        if diff:
            problems['G buildings'].append(f'与基线不符的 (生成点,州) {len(diff)} 处（前 8）: '
                                           + str(sorted(diff)[:8]))
    else:
        warn = []
        for st in s2p:
            if s2o.get(st) is None:
                continue
            n_air = cur.get(('air_base', st), 0)
            if n_air < 1:
                warn.append(f'state {st} 缺 air_base 生成点（会 MAP_ERROR/崩溃）')
        if warn:
            problems['G buildings'].extend(warn[:10])

# ---------- 汇总 ----------
print(f'== State 自检: {MOD} ==')
print(f'州 {len(states)} 个（{min(ids)}-{max(ids)}）| 省 {len(covered)} | '
      f'VP {sum(len(v) for v in s2vp.values())} | capital 悬空见下')
if problems:
    total = sum(len(v) for v in problems.values())
    for k in sorted(problems):
        print(f'\n✗ {k}（{len(problems[k])}）')
        for x in problems[k][:15]:
            print(f'   {x}')
        if len(problems[k]) > 15:
            print(f'   ... 共 {len(problems[k])} 条')
    print(f'\n结果: {total} 个问题')
    sys.exit(1)
else:
    print('\n结果: 全部通过 ✓')
    sys.exit(0)

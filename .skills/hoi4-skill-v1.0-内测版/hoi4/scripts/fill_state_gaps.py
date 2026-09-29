# -*- coding: utf-8 -*-
"""
fill_state_gaps.py v3 —— 补空白 state 编号（尾部填洞法）

规则（按用户指定）：
  1. 扫描所有 state 文件，provinces 里没有任何数字的 = 空白 state
  2. 删除这些空白 state 文件；它们的号 + 范围内缺号 = 待填空洞
  3. 把编号最大的几个州（降序取）搬到空洞号上（升序配对）
  4. 同步引用：id 行 + 文件名、国家 capital、map/buildings.txt 第 1 列、
     localisation 的 DOT_STATE_<id>（空州的具名 key 删除）

说明：HOI4 引擎本身允许 id 有空洞（原版 1.19.3 即有 112 个缺号），
本脚本只为 mod 惯例连号；尾部海州段被搬到中间后号段不连续属正常现象。

用法:
    python fill_state_gaps.py --mod <mod根目录> --dry     # 预览
    python fill_state_gaps.py --mod <mod根目录>           # 执行（自动备份）
"""
import os, re, sys, glob, shutil, datetime, argparse, collections

ap = argparse.ArgumentParser()
ap.add_argument('--mod', required=True, help='mod 根目录')
ap.add_argument('--dry', action='store_true', help='只预览不写盘')
args = ap.parse_args()
MOD = os.path.normpath(args.mod)
ST = os.path.join(MOD, 'history', 'states')
sys.stdout.reconfigure(encoding='utf-8')


def read_text(p):
    return open(p, encoding='utf-8-sig', errors='replace').read()


def write_text(p, t):
    enc = 'utf-8-sig' if open(p, 'rb').read(3) == b'\xef\xbb\xbf' else 'utf-8'
    open(p, 'wb').write(t.encode(enc))


# ---------- 1. 扫描 ----------
states = {}
for f in sorted(os.listdir(ST)):
    if not f.endswith('.txt'):
        continue
    t = read_text(os.path.join(ST, f))
    m = re.search(r'\bid\s*=\s*(\d+)', t)
    if not m:
        print(f'  !! 无法解析 id: {f}')
        continue
    sid = int(m.group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = pm.group(1).split() if pm else []
    states[sid] = (f, provs)

ids = sorted(states)
lo, hi = min(ids), max(ids)
empties = sorted(s for s, (f, pv) in states.items() if not pv)
print(f'州文件 {len(ids)} 个，范围 {lo}-{hi}')
print(f'空白 state（provinces 无数字）: {len(empties)} 个 {empties}')
missing = sorted(set(range(lo, hi + 1)) - set(ids))
print(f'缺号: {len(missing)} 个 {missing[:20]}{"..." if len(missing) > 20 else ""}')
if not empties and not missing:
    print('无空洞，无需处理。')
    sys.exit(0)

# ---------- 2. 前置安全检查 ----------
print('\n=== 前置安全检查 ===')
fatal = []
for p in glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
    t = read_text(p)
    for m in re.finditer(r'(?m)^\s*capital\s*=\s*(\d+)', t):
        if int(m.group(1)) in empties:
            fatal.append(f'{os.path.basename(p)}: capital = {m.group(1)} 指向空白 state')
if not fatal:
    print('  capital 引用 ✓')

bp = os.path.join(MOD, 'map', 'buildings.txt')
b_orphan = 0
if os.path.exists(bp):
    rawb = open(bp, 'rb').read()
    nl_s = '\r\n' if b'\r\n' in rawb else '\n'
    for l in rawb.decode('utf-8-sig').split(nl_s):
        f = l.split(';')
        if len(f) == 7 and f[0].isdigit() and int(f[0]) in empties:
            b_orphan += 1
print(f'  buildings.txt 声明空白州的条目: {b_orphan}')
if b_orphan:
    fatal.append(f'buildings.txt 有 {b_orphan} 条声明空白州（先跑转省工具的 buildings 同步）')
for x in fatal:
    print(f'  ✗ {x}')
if fatal:
    print('\n!! 先修复上述引用（capital 改到并入目标州 / buildings 跑转省同步），再跑本脚本。拒绝执行。')
    sys.exit(1)

n_named = 0
for p in glob.glob(os.path.join(MOD, 'localisation', '**', '*.yml'), recursive=True):
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', read_text(p), re.M):
        if int(m.group(1)) in empties and m.group(2) != '*':
            n_named += 1
            print(f'  ⚠ 具名「{m.group(2)}」属于空白 state {m.group(1)}，删除后丢失（先转名给并入目标）')
if not n_named:
    print('  本地化空白州名 ✓')

# ---------- 3. 搬移配对（陆海分离） ----------
holes = sorted(set(empties) | set(missing))
# 海州 = 无 owner 的州（本 mod 惯例：海州段在陆州之后）
sea_ids = sorted(s for s, (f, pv) in states.items()
                 if pv and not re.search(r'\bowner\s*=\s*\w+',
                                         read_text(os.path.join(ST, f))))
land_ids_all = [s for s in ids if s not in sea_ids and s not in empties]
sea_min = min(sea_ids) if sea_ids else hi + 1
holes_land = [h for h in holes if h < sea_min]
holes_sea = [h for h in holes if h >= sea_min]
land_pool = [s for s in land_ids_all if s not in holes][::-1]   # 陆州尾部降序
sea_pool = [s for s in sea_ids if s not in holes][::-1]         # 海州尾部降序
pairs = []
for h in holes_land:
    if land_pool:
        pairs.append((h, land_pool.pop(0)))
for h in holes_sea:
    if sea_pool:
        pairs.append((h, sea_pool.pop(0)))
leftover = len(holes) - len(pairs)
print(f'\n=== 搬移方案（陆海分离）：{len(pairs)} 对 ===')
for new, old in sorted(pairs):
    kind = '海' if new >= sea_min else '陆'
    print(f'  state {old} → state {new}（{kind}）')
if leftover:
    print(f'  ⚠ 剩余 {leftover} 个洞无同类州可填（同类州已耗尽），保持空洞')
# 过滤 old == new
pairs = [(n, o) for n, o in pairs if n != o]
moved = {o: n for n, o in pairs}
if not moved:
    print('（无需搬移，只需删除空文件）')

# ---------- 4. 其他引用报告（不改） ----------
affected = set(moved) | set(empties)
print('\n=== 其他文件引用检查（只报告） ===')
others = collections.Counter()
for root, dirs, files in os.walk(MOD):
    for f in files:
        p = os.path.join(root, f)
        rr = os.path.relpath(p, MOD)
        if rr.startswith('history') and 'states' in rr:
            continue
        if rr == os.path.join('map', 'buildings.txt'):
            continue
        if not f.endswith(('.txt', '.yml')):
            continue
        try:
            t = read_text(p)
        except Exception:
            continue
        if rr.startswith('history') and 'countries' in rr:
            continue
        hits = [int(x) for x in re.findall(r'\bstate\s*=\s*(\d+)', t) if int(x) in affected]
        if hits:
            others[rr] = len(hits)
if others:
    print('  以下文件引用了被搬/删除的州号（需人工确认）:')
    for k, v in others.most_common(20):
        print(f'    {k}: {v} 处')
else:
    print('  （无）')

if args.dry:
    print('\n[DRY] 未写盘')
    sys.exit(0)

# ---------- 5. 执行 ----------
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
par = os.path.dirname(MOD)
bdir = (os.path.join(MOD + '_backups', 'fill_gaps_' + stamp)
        if os.path.basename(par) == '.backups'
        else os.path.join(par, '.backups', 'fill_gaps_' + stamp))
os.makedirs(bdir, exist_ok=True)
print(f'\n备份目录: {bdir}')

# 5.1 删除空白 state（其名随删；具名已在检查环节提示）
for s in empties:
    f = states[s][0]
    shutil.copy2(os.path.join(ST, f), os.path.join(bdir, f))
    os.remove(os.path.join(ST, f))
print(f'已删除 {len(empties)} 个空白 state 文件')

# 5.2 搬移：改 id 行 + 重命名（先全部改成临时名避免撞号，再落正名）
for old, new in sorted(moved.items(), key=lambda x: -x[0]):
    old_f = states[old][0]
    tmp_f = f'__tmp_{old}__.txt'
    src = os.path.join(ST, old_f)
    shutil.copy2(src, os.path.join(bdir, old_f))
    os.rename(src, os.path.join(ST, tmp_f))
    t = read_text(os.path.join(ST, tmp_f))
    t = re.sub(r'(\bid\s*=\s*)\d+', rf'\g<1>{new}', t, count=1)
    write_text(os.path.join(ST, tmp_f), t)
    os.rename(os.path.join(ST, tmp_f), os.path.join(ST, f'{new}-State_{new}.txt'))
print(f'已搬移 {len(moved)} 个州')

# 5.3 capital
n_cap = 0
for p in glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
    t = read_text(p)
    t2 = re.sub(r'(?m)^(\s*capital\s*=\s*)(\d+)',
                lambda m: m.group(1) + str(moved.get(int(m.group(2)), int(m.group(2)))), t)
    if t2 != t:
        shutil.copy2(p, os.path.join(bdir, os.path.basename(p)))
        write_text(p, t2)
        n_cap += 1
print(f'capital 引用更新: {n_cap} 个国家文件')

# 5.4 buildings.txt 第 1 列
if os.path.exists(bp) and moved:
    raw = open(bp, 'rb').read()
    nl_s = '\r\n' if b'\r\n' in raw else '\n'
    lines = raw.decode('utf-8-sig').split(nl_s)
    n_b = 0
    for i, l in enumerate(lines):
        f = l.split(';')
        if len(f) == 7 and f[0].isdigit() and int(f[0]) in moved:
            f[0] = str(moved[int(f[0])])
            lines[i] = ';'.join(f)
            n_b += 1
    shutil.copy2(bp, os.path.join(bdir, 'buildings.txt'))
    open(bp, 'wb').write(nl_s.join(lines).encode('utf-8'))
    print(f'buildings.txt 州列更新: {n_b} 条')

# 5.5 本地化 DOT_STATE（删空州 key，映射被搬州，查重）
n_loc = 0
for p in glob.glob(os.path.join(MOD, 'localisation', '**', '*.yml'), recursive=True):
    t = read_text(p)
    sep = '\r\n' if '\r\n' in t else '\n'
    out, seen, dup = [], set(), 0
    for l in t.split(sep):
        m = re.match(r'^(\s*DOT_STATE_(\d+):)(.*)$', l)
        if m:
            old = int(m.group(2))
            if old in empties:
                continue                      # 空白州 key 删除
            new = moved.get(old, old)
            key = f'DOT_STATE_{new}'
            if key in seen:
                dup += 1
                continue
            seen.add(key)
            out.append(f' DOT_STATE_{new}:' + m.group(3))
            continue
        out.append(l)
    t2 = re.sub(r'(\r?\n){3,}', lambda m: m.group(1), sep.join(l.rstrip('\r') for l in out))
    if t2 != t:
        shutil.copy2(p, os.path.join(bdir, os.path.basename(p)))
        write_text(p, t2)
        n_loc += 1
        if dup:
            print(f'    {os.path.basename(p)}: 去除重复 key {dup} 条')
print(f'州名本地化更新: {n_loc} 个文件')

# ---------- 6. 终验 ----------
ids2 = []
for f in os.listdir(ST):
    if f.endswith('.txt'):
        m = re.match(r'^(\d+)-', f)
        if m:
            ids2.append(int(m.group(1)))
ids2.sort()
holes2 = sorted(set(range(min(ids2), max(ids2) + 1)) - set(ids2))
mis = []
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    fm = re.match(r'^(\d+)-', f)
    cm = re.search(r'\bid\s*=\s*(\d+)', read_text(os.path.join(ST, f)))
    if fm and cm and int(fm.group(1)) != int(cm.group(1)):
        mis.append(f)
bad_cap = []
for p in glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
    for m in re.finditer(r'(?m)^\s*capital\s*=\s*(\d+)', read_text(p)):
        if int(m.group(1)) not in set(ids2):
            bad_cap.append((os.path.basename(p), m.group(1)))
loc_keys = collections.Counter()
for p in glob.glob(os.path.join(MOD, 'localisation', '**', '*.yml'), recursive=True):
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):', read_text(p), re.M):
        loc_keys[int(m.group(1))] += 1
loc_dup = {k: v for k, v in loc_keys.items() if v > 1}
loc_orphan = sorted(k for k in loc_keys if k not in set(ids2))
tail_note = '（各段尾部自然空洞，无功能影响）' if holes2 else ''
print(f'\n终验: 州 {len(ids2)} 个，范围 {min(ids2)}-{max(ids2)}，缺号 {len(holes2)} {holes2[:10]} {tail_note}，'
      f'文件名/id 不一致 {len(mis)}')
print(f'  capital 悬空: {len(bad_cap)} {bad_cap[:5]}')
print(f'  本地化重复 key: {len(loc_dup)} {loc_dup}')
print(f'  本地化孤儿 key: {len(loc_orphan)} {loc_orphan[:5]}')
print('完成。')

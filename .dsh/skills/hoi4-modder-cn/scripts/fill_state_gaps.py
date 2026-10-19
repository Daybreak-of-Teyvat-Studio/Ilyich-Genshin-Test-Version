# -*- coding: utf-8 -*-
"""
fill_state_gaps.py v4 —— 补空白 state 编号（尾部填洞法）

规则（按用户指定）：
  1. 扫描所有 state 文件，provinces 里没有任何数字的 = 空白 state
  2. 删除这些空白 state 文件；它们的号 + 范围内缺号 = 待填空洞
  3. 把编号最大的几个州（降序取）搬到空洞号上（升序配对）
  4. 同步引用：id 行 + 文件名、国家 capital、map/buildings.txt 第 1 列、
     localisation 的 DOT_STATE_<id>（空州的具名 key 删除）
  5. 数字 id 关联的修正与脚本引用联动迁移（被搬州自动改号）：
     · 单值 token：state = N / owns_state / controls_state / has_full_control_of / transfer_state
     · 列表 token：states = { N N N }（如 ai_strategy put_unit_buffers）
     · 数字键州作用域块：<N> = { ...含州作用域标记... }（如 60 = { add_dynamic_modifier }）
     被删空州的引用无法推断并入目标，保持报告、由人工先处理。

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

# ---------- 3. 搬移配对（陆海分离 · 两步尾部换位法） ----------
# 用户方案：① 陆洞 ← 陆州尾部（降序）；② 陆州尾部空出的号 ← 海州尾部（降序）。
# 结果：陆段连续、海段连续（海段尾部自然缩短）、总体连号；只动 2k 个州。
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
used_donors = []
# 第 1 步：陆洞（升序）← 陆尾（降序）
for h in holes_land:
    if land_pool:
        d = land_pool.pop(0)
        used_donors.append(d)
        pairs.append((h, d))
# 第 2 步：被搬走的陆尾 donor 原号（升序）← 海尾（降序）
# （donor 搬走后其原号空出；这些号位于陆段尾部，用海尾接上，海段自然缩尾）
emptied_land = sorted(used_donors)
for h in emptied_land:
    if sea_pool:
        pairs.append((h, sea_pool.pop(0)))
# 海段自身的洞（罕见）：海尾（降序）填
for h in holes_sea:
    if sea_pool:
        pairs.append((h, sea_pool.pop(0)))
print(f'\n=== 搬移方案（两步尾部换位）：{len(pairs)} 对 ===')
for new, old in sorted(pairs, key=lambda x: x[1]):
    kind = '海' if new >= sea_min else '陆'
    print(f'  state {old} → state {new}（{kind}）')
# 过滤 old == new
pairs = [(n, o) for n, o in pairs if n != o]
moved = {o: n for n, o in pairs}
if not moved:
    print('（无需搬移，只需删除空文件）')

# ---------- 4. 州号引用联动迁移计划（修正 / 触发器 / 列表 / 数字键州作用域） ----------
TOKEN_RE = re.compile(r'\b(owns_state|controls_state|has_full_control_of|transfer_state|state)\s*=\s*(\d+)\b')
LIST_RE = re.compile(r'\b(states)\s*=\s*\{([^{}]*)\}')
NUMKEY_RE = re.compile(r'(?m)^([ \t]*)(\d+)[ \t]*=[ \t]*\{')
STATE_SCOPE_MARKERS = ('add_dynamic_modifier', 'set_state_owner', 'set_state_controller',
                       'transfer_state', 'add_building_construction', 'add_manpower',
                       'set_demilitarized_zone', 'set_state_name', 'create_unit',
                       'add_resistance_target', 'set_victory_points')


def blank_comments(t):
    """注释整段替换为等长空格（长度不变 → 索引与原文一一对应）。"""
    return re.sub(r'#[^\n]*', lambda m: ' ' * len(m.group(0)), t)


def block_state_scope(cmt, brace):
    """cmt[brace] 是 '{'；平衡配对返回块内是否含州作用域标记（含嵌套）。"""
    depth, i, n = 0, brace, len(cmt)
    while i < n:
        c = cmt[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                seg = cmt[brace:i]
                return any(mk in seg for mk in STATE_SCOPE_MARKERS)
        i += 1
    return False


script_rewrites = []   # (path, rel, has_bom, new_text, n_changed, [明细])
warn_refs = []         # 空州引用（无法推断并入目标）
n_ref = 0
for root, dirs, files in os.walk(MOD):
    dirs[:] = [d for d in dirs if d not in ('.backups', '.git') and '备份' not in d]
    for f in files:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(root, f)
        rr = os.path.relpath(p, MOD).replace('\\', '/')
        if rr.startswith('history/states') or rr == 'map/buildings.txt':
            continue
        raw = open(p, 'rb').read()
        t = raw.decode('utf-8-sig', errors='replace')
        cmt = blank_comments(t)
        edits = []   # (start, end, replacement, 明细)

        for m in TOKEN_RE.finditer(cmt):
            v = int(m.group(2))
            if v in moved:
                edits.append((m.start(2), m.end(2), str(moved[v]), f'{m.group(1)}={v}→{moved[v]}'))
            elif v in empties:
                warn_refs.append(f'{rr}: {m.group(1)}={v}（空州，需人工改到并入目标）')

        for m in LIST_RE.finditer(cmt):
            nums = [int(x) for x in m.group(2).split() if x.isdigit()]
            if any(v in moved for v in nums):
                new_inner = ' '.join(str(moved.get(v, v)) for v in nums)
                edits.append((m.start(), m.end(), f'{m.group(1)} = {{ {new_inner} }}',
                              f'states[{m.group(2).strip()}]→[{new_inner}]'))
            elif any(v in empties for v in nums):
                warn_refs.append(f'{rr}: states = {{ {m.group(2).strip()} }}（含空州）')

        for m in NUMKEY_RE.finditer(cmt):
            key = int(m.group(2))
            if key not in moved:
                continue
            if not block_state_scope(cmt, m.end() - 1):
                continue
            edits.append((m.start(2), m.end(2), str(moved[key]), f'{key}={moved[key]}（州作用域块）'))

        if edits:
            edits.sort()
            out, last = [], 0
            for s, e, rep, _ in edits:
                out.append(t[last:s]); out.append(rep); last = e
            out.append(t[last:])
            t2 = ''.join(out)
            script_rewrites.append((p, rr, raw[:3] == b'\xef\xbb\xbf', t2, len(edits),
                                    [d for *_, d in edits]))
            n_ref += len(edits)

print('\n=== 州号引用联动迁移（修正 / 触发器 / 列表 / 州作用域块） ===')
if not script_rewrites and not warn_refs:
    print('  （无引用需迁移）')
for p, rr, has_bom, t2, n, det in script_rewrites:
    print(f'  {rr}: {n} 处  {"  ".join(det[:6])}{" ..." if n > 6 else ""}')
for w in warn_refs:
    print(f'  ⚠ {w}')
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

# 5.2 搬移：按构造顺序分相执行（①陆洞 ← 陆尾；②被腾陆尾 ← 海尾；③海洞 ← 海尾），
#     每相内按目标号升序。禁止跨相按目标号全局排序——当洞号大于搬出者自身号
#     （洞落在尾部段内，如合并产生的 718/759）时，"他州迁入"会先于"本州迁出"执行
#     而 FileExistsError（2026-10-07 至冬重划 140 洞事故）。
seen = set()
n_moved = 0
for new, old in pairs:
    if old == new or old in seen:
        continue
    seen.add(old)
    old_f = states[old][0]
    tmp_f = f'__tmp_{old}__.txt'
    src = os.path.join(ST, old_f)
    shutil.copy2(src, os.path.join(bdir, old_f))
    os.rename(src, os.path.join(ST, tmp_f))
    t = read_text(os.path.join(ST, tmp_f))
    t = re.sub(r'(\bid\s*=\s*)\d+', rf'\g<1>{new}', t, count=1)
    # name key 同步改号（DOT_STATE_<old> → DOT_STATE_<new>），否则与本地化脱节
    t = re.sub(r'(\bname\s*=\s*")DOT_STATE_\d+(")', rf'\g<1>DOT_STATE_{new}\g<2>', t, count=1)
    write_text(os.path.join(ST, tmp_f), t)
    os.rename(os.path.join(ST, tmp_f), os.path.join(ST, f'{new}-State_{new}.txt'))
    n_moved += 1
print(f'已搬移 {n_moved} 个州（id + name key 联动）')

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
# 纯目标 id（被迁入但自身不搬的洞号）的旧占位行先让位，防重复 key
pure_targets = set(moved.values()) - set(moved.keys())
n_loc = 0
for p in glob.glob(os.path.join(MOD, 'localisation', '**', '*.yml'), recursive=True):
    t = read_text(p)
    sep = '\r\n' if '\r\n' in t else '\n'
    out, kept_name, dup = [], {}, 0
    for l in t.split(sep):
        m = re.match(r'^(\s*DOT_STATE_(\d+):)(\d*\s*"([^"]*)")', l)
        if m:
            old = int(m.group(2))
            if old in empties:
                continue                      # 空白州 key 删除
            if old in pure_targets:
                if m.group(4) != '*':
                    print(f'    ⚠ key {old} 旧名「{m.group(4)}」让位给迁入州')
                continue                      # 纯目标 id 的旧行让位
            new = moved.get(old, old)
            nm = m.group(4)
            # 覆盖式：目标 key 已有 * 占位而搬州带名 → 覆盖；反之保留先到者
            if new in kept_name:
                if kept_name[new] == '*' and nm != '*':
                    kept_name[new] = nm
                else:
                    dup += 1
                    continue
            else:
                kept_name[new] = nm
            out.append(f' DOT_STATE_{new}:0 "{kept_name[new]}"')
            continue
        out.append(l)
    t2 = re.sub(r'(\r?\n){3,}', lambda m: m.group(1), sep.join(l.rstrip('\r') for l in out))
    if t2 != t:
        shutil.copy2(p, os.path.join(bdir, os.path.basename(p)))
        write_text(p, t2)
        n_loc += 1
        if dup:
            print(f'    {os.path.basename(p)}: 覆盖 * 占位 {dup} 条')
print(f'州名本地化更新: {n_loc} 个文件')

# 5.6 州号引用联动迁移落地（修正/触发器/列表/州作用域块；BOM/CRLF 字节级保持）
for p, rr, has_bom, t2, n, det in script_rewrites:
    dst = os.path.join(bdir, rr.replace('/', '__'))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(p, dst)
    data = t2.encode('utf-8')
    if has_bom:
        data = b'\xef\xbb\xbf' + data
    open(p, 'wb').write(data)
print(f'脚本引用迁移落地: {len(script_rewrites)} 个文件，{n_ref} 处')

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

# -*- coding: utf-8 -*-
"""apply_zd_redivision.py —— 至冬 65 新州落地 + 6 组暂缓合并
1) 按涂色分组重建 SNE 州：id 按省重叠继承；manpower/资源按省数比例分摊；
   category/buildings等级/核心取重叠最大旧州；VP 按省跟随
2) 本地化"名字跟内容走"：旧州名 → N(旧州) 的 key，每个新 key 取重叠最大的旧名，其余报告丢弃
3) 首都/引用联动（旧→新全量映射，v4 同款规则）
4) 合并 6 组：省并入存留州、VP 跟省、本地化迁移、引用 A 化、删被并州文件
（补号 → fill_state_gaps；buildings 声明州/SL → rebuild_buildings_final）"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
NAMES_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')


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


def parse_state(t):
    d = {'provs': [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]}
    m = re.search(r'\bmanpower\s*=\s*([\d.]+)', t)
    d['manpower'] = float(m.group(1)) if m else 0.0
    m = re.search(r'state_category\s*=\s*(\w+)', t)
    d['cat'] = m.group(1) if m else 'wasteland'
    d['res'] = {}
    rm = re.search(r'resources\s*=\s*\{([^}]*)\}', t)
    if rm:
        for k, v in re.findall(r'(\w+)\s*=\s*([\d.]+)', rm.group(1)):
            d['res'][k] = d['res'].get(k, 0) + float(v)
    bm = re.search(r'(buildings\s*=\s*\{[^}]*)\}', t, re.S)
    d['bld'] = (bm.group(1) + '}') if bm else None
    d['vp'] = []
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        xs = vm.group(1).split()
        for i in range(0, len(xs) - 1, 2):
            d['vp'].append((int(xs[i]), int(xs[i + 1])))
    d['cores'] = re.findall(r'add_core_of\s*=\s*(\w+)', t)
    return d


# ---------- 0. 载入 ----------
div = json.load(open(os.path.join(ROOT, 'tools', 'zd_division.json'), encoding='utf-8'))
comp_provs = {int(c): sorted(v) for c, v in div['comp_provs'].items()}
old_files = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    if re.search(r'\bowner\s*=\s*SNE\b', t):
        old_files[sid] = (f, parse_state(t))
old_ids = sorted(old_files)
old_provs = {q: s for s, (_f, d) in old_files.items() for q in d['provs']}
print(f'旧 SNE 州 {len(old_ids)}，新州组件 {len(comp_provs)}')

# ---------- 1. 重叠矩阵 + id 继承 ----------
overlap = {c: collections.Counter(old_provs[q] for q in provs if q in old_provs)
           for c, provs in comp_provs.items()}
new_id, taken = {}, set()
for c in sorted(comp_provs, key=lambda c: (-max(overlap[c].values()), c)):
    for o, _n in overlap[c].most_common():
        if o not in taken:
            new_id[c] = o
            taken.add(o)
            break
assert len(new_id) == len(comp_provs)
old2new = {}
for o in old_ids:
    cands = [c for c in comp_provs if o in overlap[c]]
    best = max(cands, key=lambda c: (overlap[c][o], 1 if new_id[c] == o else 0, -c))
    old2new[o] = new_id[best]
print('id 继承完成')

# ---------- 2. 写新州文件 / 删旧 ----------
n_vp = 0
for c, provs in comp_provs.items():
    nid = new_id[c]
    hosts = collections.Counter(old_provs[q] for q in provs if q in old_provs)
    main_old = hosts.most_common(1)[0][0]
    d0 = old_files[main_old][1]
    total_mp = sum(old_files[o][1]['manpower'] * hosts[o] / len(old_files[o][1]['provs'])
                   for o in hosts)
    mp = max(0, int(round(total_mp / 1000.0)) * 1000)
    res = collections.defaultdict(float)
    for o in hosts:
        d1 = old_files[o][1]
        for k, v in d1['res'].items():
            res[k] += v * hosts[o] / len(d1['provs'])
    res_s = ''.join(f'\t\t{k} = {int(round(v))}\r\n' for k, v in sorted(res.items()) if round(v) > 0)
    vp_pairs = sorted({(pid, val) for o in hosts for pid, val in old_files[o][1]['vp']
                       if pid in set(provs)})
    n_vp += len(vp_pairs)
    vp_s = ''.join(f'\t\tvictory_points = {{ {pid} {val} }}\r\n' for pid, val in vp_pairs)
    bld_s = d0['bld'] + '\r\n' if d0['bld'] else ''
    cores = ['SNE'] + [x for x in d0['cores'] if x != 'SNE']
    core_s = ''.join(f'\t\tadd_core_of = {x}\r\n' for x in dict.fromkeys(cores))
    t = (f'state = {{\r\n'
         f'\tid = {nid}\r\n'
         f'\tname="DOT_STATE_{nid}"\r\n'
         f'\tmanpower = {mp}\r\n'
         f'\tstate_category = {d0["cat"]}\r\n'
         + (f'\tresources = {{\r\n{res_s}\t}}\r\n' if res_s else '')
         + f'\r\n\thistory = {{\r\n'
           f'\t\towner = SNE\r\n{core_s}{bld_s}{vp_s}'
           f'\t}}\r\n\r\n'
           f'\tprovinces = {{\r\n\t\t{" ".join(str(q) for q in provs)}\r\n\t}}\r\n'
           f'}}\r\n')
    save(os.path.join(ST, f'{nid}-State_{nid}.txt'), t, False)
for o in old_ids:
    os.remove(os.path.join(ST, old_files[o][0]))
print(f'写新州 {len(comp_provs)} 个文件，删旧 {len(old_ids)} 个；VP 迁移 {n_vp} 条')

# ---------- 3. 本地化：名字跟内容走 ----------
raw, t = load(NAMES_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
cur_name = {int(m.group(1)): m.group(2) for m in
            re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', t, re.M)}
comp_of_id = {new_id[c]: c for c in comp_provs}
target = {}   # 新id -> (overlap, name)  名字跟内容走
for o in old_ids:
    nm = cur_name.get(o, '*')
    if nm == '*':
        continue
    I = old2new[o]
    ov = overlap[comp_of_id[I]][o]
    if I not in target or ov > target[I][0]:
        target[I] = (ov, nm)
lost = []      # 落选的名字
for o in old_ids:
    nm = cur_name.get(o, '*')
    if nm != '*' and cur_name.get(old2new[o], '*') != nm:
        lost.append((o, nm))
out, dropped = [], []
for l in t.split(nl):
    m = re.match(r'^(\s*DOT_STATE_(\d+):)\d*(\s*)"([^"]*)"', l)
    if m:
        k = int(m.group(2))
        if k in old_files:                     # 旧 SNE id 的 key 全部按 target 重写
            if k in target:
                nm = target[k][1]
                if cur_name.get(k, '*') != nm:
                    dropped.append((k, cur_name.get(k, '*'), nm))
                l = f'{m.group(1)}0{m.group(3)}"{nm}"'
            else:
                l = f'{m.group(1)}0{m.group(3)}"*"'   # 无名可继 → 占位
    out.append(l)
save(NAMES_F, nl.join(out), has_bom)
print(f'本地化: 重写 {len(old_files)} 个 key；换名 {len(dropped)} 处；落选名字 {len(lost)} 个')
for o, nm in lost:
    print(f'  ✗「{nm}」(旧s{o}) 未能在 s{old2new[o]} 胜出，丢弃')
for k, old, new in dropped:
    print(f'  s{k}: 「{old}」→「{new}」')

# ---------- 4. 首都 ----------
moved = dict(old2new)
cap_hits = []
for p in glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    t2 = re.sub(r'(?m)^(\s*capital\s*=\s*)(\d+)',
                lambda mm: mm.group(1) + str(moved.get(int(mm.group(2)), int(mm.group(2)))), t)
    if t2 != t:
        save(p, t2, open(p, 'rb').read()[:3] == b'\xef\xbb\xbf')
        cap_hits.append(os.path.basename(p))
print(f'首都联动: {cap_hits or "无变更"}')

# ---------- 5. 引用迁移 ----------
TOKEN_RE = re.compile(r'\b(owns_state|controls_state|has_full_control_of|transfer_state|state)\s*=\s*(\d+)\b')
LIST_RE = re.compile(r'\b(states)\s*=\s*\{([^{}]*)\}')
NUMKEY_RE = re.compile(r'(?m)^([ \t]*)(\d+)[ \t]*=[ \t]*\{')
MARKERS = ('add_dynamic_modifier', 'set_state_owner', 'set_state_controller', 'transfer_state',
           'add_building_construction', 'add_manpower', 'set_demilitarized_zone',
           'set_state_name', 'create_unit', 'add_resistance_target', 'set_victory_points')


def blank_comments(t):
    return re.sub(r'#[^\n]*', lambda m: ' ' * len(m.group(0)), t)


def block_state_scope(cmt, brace):
    depth, i = 0, brace
    while i < len(cmt):
        c = cmt[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return any(mk in cmt[brace:i] for mk in MARKERS)
        i += 1
    return False


def migrate_refs(moved_map, tag):
    n_f = n_r = 0
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
            edits = []
            for m in TOKEN_RE.finditer(cmt):
                v = int(m.group(2))
                if v in moved_map:
                    edits.append((m.start(2), m.end(2), str(moved_map[v])))
            for m in LIST_RE.finditer(cmt):
                nums = [int(x) for x in m.group(2).split() if x.isdigit()]
                if any(v in moved_map for v in nums):
                    new_inner = ' '.join(str(moved_map.get(v, v)) for v in nums)
                    edits.append((m.start(), m.end(), f'{m.group(1)} = {{ {new_inner} }}'))
            for m in NUMKEY_RE.finditer(cmt):
                k = int(m.group(2))
                if k in moved_map and block_state_scope(cmt, m.end() - 1):
                    edits.append((m.start(2), m.end(2), str(moved_map[k])))
            if edits:
                edits.sort()
                out, last = [], 0
                for s, e, rep in edits:
                    out.append(t[last:s]); out.append(rep); last = e
                out.append(t[last:])
                data = ''.join(out).encode('utf-8')
                open(p, 'wb').write((b'\xef\xbb\xbf' + data) if raw[:3] == b'\xef\xbb\xbf' else data)
                n_f += 1
                n_r += len(edits)
    print(f'引用联动[{tag}]: {n_f} 个文件 {n_r} 处')


migrate_refs(moved, '至冬重划')

# ---------- 6. 合并 6 组 ----------
MERGES = [(583, 603), (718, 552), (567, 550), (568, 550), (72, 70), (507, 526), (759, 735)]
moved_m = {b: a for b, a in MERGES}
files = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    files[sid] = (f, t)
for b, a in MERGES:
    fb, tb = files[b]
    fa, ta = files[a]
    pb = re.search(r'provinces\s*=\s*\{([^}]*)\}', tb).group(1).split()
    pa = re.search(r'(provinces\s*=\s*\{)([^}]*)(\})', ta)
    provs = pa.group(2).split() + pb
    ta = ta[:pa.start()] + pa.group(1) + '\r\n\t\t' + ' '.join(provs) + '\r\n\t' + pa.group(3) + ta[pa.end():]
    close = history_close(ta)
    for vm in re.finditer(r'[ \t]*victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}[ \t]*\r?\n?', tb):
        pid, val = vm.group(1), vm.group(2)
        if f'victory_points = {{ {pid} ' in ta:
            continue
        ls = ta.rfind('\n', 0, close) + 1
        ta = ta[:ls] + f'\t\tvictory_points = {{ {pid} {val} }}\r\n' + ta[ls:]
        close = history_close(ta)
    save(os.path.join(ST, fa), ta, open(os.path.join(ST, fa), 'rb').read()[:3] == b'\xef\xbb\xbf')
    os.remove(os.path.join(ST, fb))
    print(f'合并 s{b} → s{a}（{len(pb)} 省并入）')
# 合并本地化
raw, t = load(NAMES_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
cur_name = {int(m.group(1)): m.group(2) for m in
            re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', t, re.M)}
out = []
for l in t.split(nl):
    m = re.match(r'^(\s*DOT_STATE_(\d+):)\d*(\s*)"([^"]*)"', l)
    if m:
        o, nm = int(m.group(2)), m.group(4)
        if o in moved_m:
            if nm == '*':
                continue
            a = moved_m[o]
            if cur_name.get(a, '*') == '*':
                l = f'{m.group(1)}0{m.group(3)}"{nm}"'
                cur_name[a] = nm
            else:
                print(f'  合并名冲突丢弃: 「{nm}」(s{o})，s{a} 保留「{cur_name[a]}」')
                continue
    out.append(l)
save(NAMES_F, nl.join(out), has_bom)
# 合并首都
for p in glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    t2 = re.sub(r'(?m)^(\s*capital\s*=\s*)(\d+)',
                lambda mm: mm.group(1) + str(moved_m.get(int(mm.group(2)), int(mm.group(2)))), t)
    if t2 != t:
        save(p, t2, open(p, 'rb').read()[:3] == b'\xef\xbb\xbf')
# 合并引用（单值 token 即可：被并州数量少）
for p in glob.glob(os.path.join(MOD, 'common', '**', '*.txt'), recursive=True) + \
         glob.glob(os.path.join(MOD, 'events', '*.txt')) + \
         glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
    rr = os.path.relpath(p, MOD).replace('\\', '/')
    if rr == 'map/buildings.txt':
        continue
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig', errors='replace')
    t2 = TOKEN_RE.sub(lambda m: m.group(0) if int(m.group(2)) not in moved_m
                      else m.group(1) + ' = ' + str(moved_m[int(m.group(2))]), t)
    if t2 != t:
        data = t2.encode('utf-8')
        open(p, 'wb').write((b'\xef\xbb\xbf' + data) if raw[:3] == b'\xef\xbb\xbf' else data)
print('合并收尾完成（首都/引用/本地化）')
print('全脚本完成——补号与 buildings 重整交给后续脚本')

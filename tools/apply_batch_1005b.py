# -*- coding: utf-8 -*-
"""apply_batch_1005b.py —— VP 批次：15 加 + 3 清除 + 4 首都标记，按指令顺序处理

规矩：括号=VP（省号,名,数值[,首都]）；`省号*` = VP 清除（值+本地化 key）。
首都：同国多标记按指令顺序取最后生效。735+759=735 合并暂缓未动。
"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
VP_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

# (操作, 省, 名, 值, 首都) —— 按指令顺序；名=None 表示清除
ITEMS = [
    ('add', 2070, '受侵蚀的石室', 5, False),
    ('del', 1482, None, None, False),
    ('add', 4315, '曜石图腾柱·花羽会', 25, True),
    ('add', 1527, '翘枝崖神像', 20, False),
    ('add', 1243, '曜石图腾柱·烟谜主', 25, True),
    ('del', 2149, None, None, False),
    ('add', 4319, '话事处', 25, True),
    ('add', 1857, '煅石之轮', 15, False),
    ('del', 4310, None, None, False),
    ('add', 4330, '茜特菈莉的住处', 15, False),
    ('add', 749, '镜璧山神像', 20, False),
    ('add', 1171, '碑碣的记录', 20, False),
    ('add', 4284, '隐世修行之处', 5, False),
    ('add', 4370, '熔烈的罅隙', 5, False),
    ('add', 1003, '虹灵的净土', 15, False),
    ('add', 4484, '曜石图腾柱·流泉之众', 25, True),
    ('add', 1589, '涌流地神像', 20, False),
    ('add', 4422, '漫野的洞窟', 5, False),
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


p2s = {}
owners = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        p2s[int(x)] = sid
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    owners[sid] = om.group(1) if om else None

# ---------- 1. state 文件 VP 增删 ----------
touched = {}   # sid -> (raw, text, has_bom)
for op, pid, nm, val, cap in ITEMS:
    h = p2s.get(pid)
    assert h, f'p{pid} 不在任何州'
    if h not in touched:
        raw, t = load(os.path.join(ST, f'{h}-State_{h}.txt'))
        touched[h] = (raw, t, raw[:3] == b'\xef\xbb\xbf')
    raw, t, has_bom = touched[h]
    cur = vps_of(t).get(pid)
    if op == 'del':
        if cur is None:
            print(f'  清除 p{pid}: 本来就没有 VP ✓')
        else:
            pat = re.compile(r'[ \t]*victory_points\s*=\s*\{\s*' + str(pid) + r'\s+\d+\s*\}[ \t]*\r?\n?')
            t, n = pat.subn('', t)
            print(f'  清除 p{pid}: s{h} 删条目 ×{n}（原值 {cur}）')
        touched[h] = (raw, t, has_bom)
    else:
        if cur == val:
            print(f'  加 p{pid}「{nm}」{val}: s{h} 已有 ✓')
        elif cur is None:
            ls = t.rfind('\n', 0, history_close(t)) + 1
            t = t[:ls] + f'\t\tvictory_points = {{ {pid} {val} }}\r\n' + t[ls:]
            print(f'  加 p{pid}「{nm}」{val}: 写入 s{h} ✓')
        else:
            print(f'  ⚠ p{pid}: s{h} 现值 {cur} ≠ {val}，未动')
        touched[h] = (raw, t, has_bom)

for sid, (raw, t, has_bom) in touched.items():
    save(os.path.join(ST, f'{sid}-State_{sid}.txt'), t, has_bom)

# ---------- 2. VP 本地化：删 3 加 15 ----------
del_pids = [pid for op, pid, nm, _, _ in ITEMS if op == 'del']
loc_add = [(pid, nm) for op, pid, nm, _, _ in ITEMS if op == 'add']
raw, t = load(VP_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
out, ndel = [], 0
for l in t.split(nl):
    m = re.match(r'^\s*VICTORY_POINTS_(\d+):', l)
    if m and int(m.group(1)) in del_pids:
        ndel += 1
        continue
    out.append(l)
have = {int(m.group(1)): m.group(2) for l in out if (m := re.match(r'^\s*VICTORY_POINTS_(\d+):\d*\s+"([^"]*)"', l))}
nadd = 0
for pid, nm in loc_add:
    if pid in have:
        if have[pid] != nm:
            print(f'  ⚠ VICTORY_POINTS_{pid} 现为「{have[pid]}」≠「{nm}」，未动')
        continue
    out.append(f' VICTORY_POINTS_{pid}:0 "{nm}"')
    nadd += 1
save(VP_F, nl.join(out), has_bom)
print(f'VP 本地化: 删 {ndel}，加 {nadd}')

# ---------- 3. 首都（按指令顺序，后写覆盖先写） ----------
caps = {}
for op, pid, nm, val, cap in ITEMS:
    if cap:
        caps[owners[p2s[pid]]] = p2s[pid]     # 后面的覆盖前面的（同 tag）
for tag, sid in caps.items():
    hits = glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag} - *.txt')) or \
           glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag}*.txt'))
    assert hits, f'{tag} 国家历史文件没找到'
    p = hits[0]
    raw, t = load(p)
    t2, n = re.subn(r'(?m)^(\s*capital\s*=\s*)\d+', rf'\g<1>{sid}', t, count=1)
    if n == 0:
        t2 = t.rstrip('\r\n') + '\r\n\tcapital = ' + str(sid) + '\r\n'
    save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'  首都: {tag} capital = {sid}')

# ---------- 4. 回读验证 ----------
print()
print('=== 回读验证 ===')
errs = 0
vp_all = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        xs = vm.group(1).split()
        for i in range(0, len(xs) - 1, 2):
            vp_all[(sid, int(xs[i]))] = int(xs[i + 1])
vp_t = open(VP_F, encoding='utf-8-sig').read()
have = {int(m.group(1)): m.group(2) for m in
        (re.match(r'^\s*VICTORY_POINTS_(\d+):\d*\s+"([^"]*)"', l) for l in vp_t.splitlines()) if m}
for op, pid, nm, val, cap in ITEMS:
    h = p2s[pid]
    if op == 'del':
        ok = (h, pid) not in vp_all and pid not in have
        print(f'  清除 p{pid}: {"✓" if ok else "✗ 仍有残留"}')
    else:
        ok = vp_all.get((h, pid)) == val and have.get(pid) == nm
        print(f'  加 p{pid}「{nm}」{val}: s{h} {"✓" if ok else "✗"}')
    errs += not ok
for tag, sid in caps.items():
    t = open(glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag}*.txt'))[0],
             encoding='utf-8-sig').read()
    m = re.search(r'(?m)^\s*capital\s*=\s*(\d+)', t)
    ok = m and int(m.group(1)) == sid
    print(f'  首都 {tag}={sid}: {"✓" if ok else "✗ 现为 " + (m.group(1) if m else "无")}')
    errs += not ok
print('\n全部通过 ✓' if errs == 0 else f'\n{errs} 项失败 ✗')

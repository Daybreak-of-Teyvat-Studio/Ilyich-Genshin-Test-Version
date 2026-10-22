# -*- coding: utf-8 -*-
"""apply_batch_1005c.py —— 批次：转省 2 + 州名 1 + VP 18（15 加/2 清/2 首都）
落地后逐条回读验证"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
NAMES_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VP_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
BP = os.path.join(MOD, 'map', 'buildings.txt')

TRANSFERS = [(446, 709), (4160, 708)]
NAMES = [(708, '分道誓约之厅')]
# (op, 省, 名, 值, 首都)
ITEMS = [
    ('add', 1082, '曜石图腾柱·悬木人', 25, True),
    ('add', 2005, '石山之中', 10, False),
    ('add', 732, '踞石山神像', 20, False),
    ('add', 4392, '幻写画之地', 10, False),
    ('add', 4374, '遗留庙宇的祭奠所', 10, False),
    ('add', 1142, '开采研究所·实验区', 10, False),
    ('add', 2414, '开采研究所·通道', 10, False),
    ('add', 4255, '古旧发掘处', 10, False),
    ('add', 554, '歇息处的入口', 10, False),
    ('add', 2259, '蕴火的幽墟', 15, False),
    ('add', 4274, '火榴树根系', 10, False),
    ('add', 400, '深古瞭望所', 15, False),
    ('del', 4185, None, None, False),
    ('del', 313, None, None, False),
    ('add', 4219, '特菈佐莉特拉佐莉的铸造工坊', 10, False),
    ('add', 4177, '坚岩隘谷神像', 25, False),
    ('add', 4148, '曜石图腾柱·回声之子', 25, True),
    ('add', 2365, '圣途试炼遗迹', 10, False),
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


# ---------- 1. 转省（含 buildings 第 1 列同步） ----------
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
    print(f'转省 p{pid}: s{src}→s{dst}，buildings 同步 {nb} 条')

# ---------- 2. 州名 ----------
raw, t = load(NAMES_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
nm_map = dict(NAMES)
out = []
for l in t.split(nl):
    m = re.match(r'^(\s*DOT_STATE_(\d+):)0?(\s*)"([^"]*)"', l)
    if m and int(m.group(2)) in nm_map:
        sid = int(m.group(2))
        cur, want = m.group(4), nm_map[sid]
        if cur == want:
            print(f'  s{sid}「{want}」已是 ✓')
        elif cur == '*':
            l = f'{m.group(1)}0{m.group(3)}"{want}"'
            print(f'  s{sid}「{want}」写入 ✓')
        else:
            print(f'  ⚠ s{sid} 现名「{cur}」≠「{want}」，未动')
    out.append(l)
save(NAMES_F, nl.join(out), has_bom)

# ---------- 3. VP 增删 ----------
p2s = {}
owners = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for x in provs_of(t):
        p2s[int(x)] = sid
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    owners[sid] = om.group(1) if om else None
touched = {}
for op, pid, nm, val, cap in ITEMS:
    h = p2s[pid]
    if h not in touched:
        r2, t2 = load(os.path.join(ST, f'{h}-State_{h}.txt'))
        touched[h] = (r2, t2, r2[:3] == b'\xef\xbb\xbf')
    raw, t, has_bom = touched[h]
    cur = vps_of(t).get(pid)
    if op == 'del':
        if cur is None:
            print(f'  清除 p{pid}: 本来就没有 ✓')
        else:
            t, n = re.subn(r'[ \t]*victory_points\s*=\s*\{\s*' + str(pid) + r'\s+\d+\s*\}[ \t]*\r?\n?', '', t)
            print(f'  清除 p{pid}: s{h} 删 ×{n}（原值 {cur}）')
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

# ---------- 4. VP 本地化 ----------
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
            print(f'  ⚠ VP key p{pid} 现为「{have[pid]}」≠「{nm}」，未动')
        continue
    out.append(f' VICTORY_POINTS_{pid}:0 "{nm}"')
    nadd += 1
save(VP_F, nl.join(out), has_bom)
print(f'VP 本地化: 删 {ndel}，加 {nadd}')

# ---------- 5. 首都 ----------
caps = {}
for op, pid, nm, val, cap in ITEMS:
    if cap:
        caps[owners[p2s[pid]]] = p2s[pid]
for tag, sid in caps.items():
    p = glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag}*.txt'))[0]
    raw, t = load(p)
    t2, n = re.subn(r'(?m)^(\s*capital\s*=\s*)\d+', rf'\g<1>{sid}', t, count=1)
    save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'首都: {tag} = s{sid}')

# ---------- 6. 回读验证 ----------
print()
print('=== 回读验证 ===')
errs = 0
vp_all = {}
p2s2 = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for x in provs_of(t):
        p2s2[int(x)] = sid
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        xs = vm.group(1).split()
        for i in range(0, len(xs) - 1, 2):
            vp_all[(sid, int(xs[i]))] = int(xs[i + 1])
for pid, dst in TRANSFERS:
    ok = p2s2.get(pid) == dst
    print(f'转省 p{pid}→s{dst}: {"✓" if ok else "✗ 现在在 s" + str(p2s2.get(pid))}')
    errs += not ok
nm_t = open(NAMES_F, encoding='utf-8-sig').read()
for sid, nm in NAMES:
    ok = re.search(rf'DOT_STATE_{sid}:0\s*"{re.escape(nm)}"', nm_t) is not None
    print(f'州名 s{sid}「{nm}」: {"✓" if ok else "✗"}')
    errs += not ok
vp_t = open(VP_F, encoding='utf-8-sig').read()
have = {int(m.group(1)): m.group(2) for m in
        (re.match(r'^\s*VICTORY_POINTS_(\d+):\d*\s+"([^"]*)"', l) for l in vp_t.splitlines()) if m}
for op, pid, nm, val, cap in ITEMS:
    h = p2s2[pid]
    if op == 'del':
        ok = (h, pid) not in vp_all and pid not in have
        print(f'清除 p{pid}: {"✓" if ok else "✗ 残留"}')
    else:
        ok = vp_all.get((h, pid)) == val and have.get(pid) == nm
        print(f'加 p{pid}「{nm}」{val}: s{h} {"✓" if ok else "✗"}')
    errs += not ok
for tag, sid in caps.items():
    t = open(glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag}*.txt'))[0],
             encoding='utf-8-sig').read()
    m = re.search(r'(?m)^\s*capital\s*=\s*(\d+)', t)
    ok = m and int(m.group(1)) == sid
    print(f'首都 {tag}=s{sid}: {"✓" if ok else "✗"}')
    errs += not ok
print('\n全部通过 ✓' if errs == 0 else f'\n{errs} 项失败 ✗')

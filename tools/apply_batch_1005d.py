# -*- coding: utf-8 -*-
"""apply_batch_1005d.py —— 批次：州名 2（含 s708 改名覆盖）+ VP 19（含 p1137 改值 25→50、p2407 首都）

用户指令即权威：州名覆盖现值；VP 括号里的数值就是最终值（现值不同 = 改值）。
"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
NAMES_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VP_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

NAMES = [(708, '分道誓约之地'), (730, '火榴大母树')]
# (省, 名, 值, 首都)
ITEMS = [
    (902, '众岩之里', 10, False),
    (1628, '山脉的横裂', 10, False),
    (1912, '踞石山之底', 10, False),
    (25, '万火之瓯神像', 20, False),
    (104, '灵壁的洞窟', 5, False),
    (2407, '曜石图腾柱·沃陆之邦', 25, True),
    (2230, '安饶之野神像', 20, False),
    (4464, '穿山甬道北口', 15, False),
    (4519, '穿山甬道南口', 15, False),
    (1137, '远古圣山', 50, False),
    (350, '荒废砌造坞', 15, False),
    (4605, '秘源机兵·统御械', 20, False),
    (440, '噩梦的温床', 10, False),
    (3932, '天蛇船', 25, False),
    (1711, '源火之圣座', 25, False),
    (297, '统律之心·内里', 10, False),
    (2405, '炽火燃尽所·其三', 10, False),
    (763, '炽火燃尽所·其三', 10, False),
    (1880, '奥奇卡纳塔神像', 20, False),
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


# ---------- 1. 州名（覆盖语义） ----------
raw, t = load(NAMES_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
nm_map = dict(NAMES)
out = []
for l in t.split(nl):
    m = re.match(r'^(\s*DOT_STATE_(\d+):)0?(\s*)"([^"]*)"', l)
    if m and int(m.group(2)) in nm_map:
        sid = int(m.group(2))
        want = nm_map[sid]
        if m.group(4) != want:
            print(f'  s{sid}: 「{m.group(4)}」→「{want}」')
            l = f'{m.group(1)}0{m.group(3)}"{want}"'
        else:
            print(f'  s{sid}「{want}」已是 ✓')
    out.append(l)
save(NAMES_F, nl.join(out), has_bom)

# ---------- 2. VP（含改值） ----------
p2s, owners = {}, {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for x in provs_of(t):
        p2s[int(x)] = sid
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    owners[sid] = om.group(1) if om else None
touched = {}
for pid, nm, val, cap in ITEMS:
    h = p2s.get(pid)
    assert h, f'p{pid} 不在任何州'
    if h not in touched:
        r2, t2 = load(os.path.join(ST, f'{h}-State_{h}.txt'))
        touched[h] = (r2, t2, r2[:3] == b'\xef\xbb\xbf')
    raw, t, has_bom = touched[h]
    cur = vps_of(t).get(pid)
    if cur == val:
        print(f'  p{pid}「{nm}」{val}: s{h} 已有 ✓')
    elif cur is None:
        ls = t.rfind('\n', 0, history_close(t)) + 1
        t = t[:ls] + f'\t\tvictory_points = {{ {pid} {val} }}\r\n' + t[ls:]
        print(f'  p{pid}「{nm}」{val}: 写入 s{h} ✓')
    else:
        t = re.sub(r'(victory_points\s*=\s*\{\s*)' + str(pid) + r'\s+\d+(\s*\})',
                   rf'\g<1>{pid} {val}\g<2>', t)
        print(f'  p{pid}「{nm}」: s{h} 改值 {cur}→{val} ✓')
    touched[h] = (raw, t, has_bom)
for sid, (raw, t, has_bom) in touched.items():
    save(os.path.join(ST, f'{sid}-State_{sid}.txt'), t, has_bom)

# ---------- 3. VP 本地化（存在即更新为指令名） ----------
raw, t = load(VP_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
want = {pid: nm for pid, nm, _, _ in ITEMS}
out, nupd, nadd = [], 0, 0
for l in t.split(nl):
    m = re.match(r'^(\s*VICTORY_POINTS_(\d+):)\d*(\s*)"([^"]*)"', l)
    if m and int(m.group(2)) in want:
        pid = int(m.group(2))
        if m.group(4) != want[pid]:
            print(f'  VP key p{pid}: 「{m.group(4)}」→「{want[pid]}」')
            l = f'{m.group(1)}0{m.group(3)}"{want[pid]}"'
            nupd += 1
        want.pop(pid)
    out.append(l)
for pid, nm in want.items():
    out.append(f' VICTORY_POINTS_{pid}:0 "{nm}"')
    nadd += 1
save(VP_F, nl.join(out), has_bom)
print(f'VP 本地化: 更新 {nupd}，新增 {nadd}')

# ---------- 4. 首都 ----------
caps = {}
for pid, nm, val, cap in ITEMS:
    if cap:
        caps[owners[p2s[pid]]] = p2s[pid]
for tag, sid in caps.items():
    p = glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag}*.txt'))[0]
    raw, t = load(p)
    t2, n = re.subn(r'(?m)^(\s*capital\s*=\s*)\d+', rf'\g<1>{sid}', t, count=1)
    save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'首都: {tag} = s{sid}')

# ---------- 5. 回读验证 ----------
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
nm_t = open(NAMES_F, encoding='utf-8-sig').read()
vp_t = open(VP_F, encoding='utf-8-sig').read()
for sid, nm in NAMES:
    ok = re.search(rf'DOT_STATE_{sid}:0\s*"{re.escape(nm)}"', nm_t) is not None
    print(f'州名 s{sid}「{nm}」: {"✓" if ok else "✗"}')
    errs += not ok
for pid, nm, val, cap in ITEMS:
    h = p2s[pid]
    ok = vp_all.get((h, pid)) == val and \
        re.search(rf'VICTORY_POINTS_{pid}:0\s*"{re.escape(nm)}"', vp_t) is not None
    print(f'p{pid}「{nm}」{val}: s{h} {"✓" if ok else "✗"}')
    errs += not ok
for tag, sid in caps.items():
    t = open(glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag}*.txt'))[0],
             encoding='utf-8-sig').read()
    m = re.search(r'(?m)^\s*capital\s*=\s*(\d+)', t)
    ok = m and int(m.group(1)) == sid
    print(f'首都 {tag}=s{sid}: {"✓" if ok else "✗"}')
    errs += not ok
print('\n全部通过 ✓' if errs == 0 else f'\n{errs} 项失败 ✗')

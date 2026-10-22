# -*- coding: utf-8 -*-
"""VP 任务：删全部胜利点 → 16 省 25 值 VP + 本地化 + set_capital。"""
import os, re, sys, shutil, datetime, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
CD = os.path.join(G, 'history', 'countries')

VP = [(1808, '至高神座'), (860, '深境螺旋'), (292, '骑士团总部'), (3410, '星落湖神像'),
      (1601, '荆夫港'), (442, '孤王的高塔'), (3529, '王狼领地'), (1189, '晨曦酒庄'),
      (1015, '清泉镇中心'), (1661, '达达乌帕谷剑冢'), (1463, '寒天之钉'), (2463, '玉京台'),
      (3452, '遗珑埠'), (1096, '黑岩厂'), (3974, '净善宫'), (2027, '桓那兰那')]
VP_BY_PID = dict(VP)

s2p, s2o, raw = {}, {}, {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2o[sid] = re.search(r'\bowner\s*=\s*(\w+)', t).group(1)
    s2p[sid] = [int(x) for x in re.search(r'provinces = \{([^}]*)\}', t).group(1).split()]
    raw[sid] = t
p2s = {p: s for s, ps in s2p.items() for p in ps}

vp_state = collections.defaultdict(list)
for pid, cn in VP:
    s = p2s.get(pid)
    assert s, f'省 {pid} 不在任何州'
    vp_state[s].append((pid, cn))

bdir = os.path.join(ROOT, '.backups', 'vp_reset_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)


def set_vps_line(t, vps):
    """vps: [(pid, val)]；无则整行删。返回新文本。"""
    line = ('victory_points = { ' + ' '.join(f'{p} {v}' for p, v in sorted(vps)) + ' }') if vps else None
    if re.search(r'victory_points = \{[^}]*\}', t):
        if line:
            return re.sub(r'victory_points = \{[^}]*\}', line, t)
        return re.sub(r'\r\n\t\tvictory_points = \{[^}]*\}', '', t)
    if not line:
        return t
    hm = re.search(r'\thistory = \{', t)
    depth, i, end = 0, hm.end() - 1, None
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
        i += 1
    ls = t.rfind('\r\n', 0, end) + 2
    return t[:ls] + '\t\t' + line + '\r\n' + t[ls:]


changed = 0
for sid in sorted(s2p):
    t = raw[sid]
    vps = vp_state.get(sid, [])
    nt = set_vps_line(t, vps)
    if nt != t:
        shutil.copy2(os.path.join(ST, f'{sid}-State_{sid}.txt'), os.path.join(bdir, f'{sid}-State_{sid}.txt'))
        with open(os.path.join(ST, f'{sid}-State_{sid}.txt'), 'w', encoding='utf-8', newline='') as fh:
            fh.write(nt)
        changed += 1
print(f'胜利点重写：{changed} 个州文件（全删 + 16 州 25 值），备份 {bdir}')

# ---- set_capital ----
for sid in sorted(vp_state):
    tag = s2o[sid]
    cdir = None
    for f in os.listdir(CD):
        if f.upper().startswith(tag):
            cdir = f
            break
    assert cdir, f'{tag} 国家文件未找到'
    fp = os.path.join(CD, cdir)
    t = open(fp, encoding='utf-8-sig', newline='').read()
    if re.search(r'(?m)^\s*capital\s*=', t):
        t2 = re.sub(r'(?m)^(\s*capital\s*=\s*)\d+', rf'\g<1>{sid}', t, count=1)
    else:
        t2 = t.rstrip('\r\n') + f'\r\n\r\ncapital = {sid}\r\n'
    if t2 != t:
        shutil.copy2(fp, os.path.join(bdir, cdir))
        with open(fp, 'w', encoding='utf-8', newline='') as fh:
            fh.write(t2)
        print(f'  {tag}: capital = {sid}')

# ---- 本地化 ----
LOC = os.path.join(G, 'localisation', 'simp_chinese')
target = None
for f in os.listdir(LOC):
    if 'victory' in f.lower() and f.endswith('.yml'):
        target = f
        break
if not target:
    target = 'DOT_Victory_Points_gamma_l_simp_chinese.yml'
lp = os.path.join(LOC, target)
need = [(pid, cn) for pid, cn in VP]
have = set()
if os.path.exists(lp):
    cur = open(lp, encoding='utf-8-sig', errors='replace').read()
    for pid, cn in need:
        if f'VICTORY_POINTS_{pid}:' in cur:
            have.add(pid)
missing = [(p, c) for p, c in need if p not in have]
if missing:
    add = '\r\n'.join(f' VICTORY_POINTS_{pid}:0 "{cn}"' for pid, cn in missing)
    raw2 = open(lp, 'rb').read() if os.path.exists(lp) else b'\xef\xbb\xbfl_simp_chinese:\r\n'
    if not os.path.exists(lp):
        open(lp, 'wb').write(raw2)
        cur = raw2.decode('utf-8-sig')
    else:
        cur = open(lp, encoding='utf-8-sig', errors='replace').read()
    open(lp, 'wb').write((cur.rstrip('\r\n') + '\r\n' + add + '\r\n').encode('utf-8'))
    print(f'本地化：{target} 追加 {len(missing)} 条 VICTORY_POINTS_*')
else:
    print('本地化已齐全')

# ---- 复验 ----
tot = 0
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    for m in re.finditer(r'victory_points = \{([^}]*)\}', t):
        tot += len(m.group(1).split()) // 2
print(f'复验：全 mod 胜利点 {tot} 个（应 16）')
for pid, cn in VP:
    s = p2s[pid]
    t = open(os.path.join(ST, f'{s}-State_{s}.txt'), encoding='utf-8-sig', newline='').read()
    m = re.search(r'victory_points = \{([^}]*)\}', t)
    ok = m and f'{pid} 25' in m.group(1)
    print(f'  省 {pid} {cn}: state {s} {"✓ 25值" if ok else "✗ " + (m.group(1) if m else "无VP")}')

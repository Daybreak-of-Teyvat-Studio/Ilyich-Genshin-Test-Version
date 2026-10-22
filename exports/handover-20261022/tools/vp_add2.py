# -*- coding: utf-8 -*-
"""13 个新 VP（25 值）+ 本地化 + set_capital（在最新归属上判定所属州/owner）。"""
import os, re, sys, shutil, datetime, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
CD = os.path.join(G, 'history', 'countries')

VP = [(140, '阿如村'), (2275, '塔尼特露营地'), (494, '万种母树'), (1834, '沫芒宫'),
      (4319, '话事处'), (4148, '回声之子'), (4154, '花羽会'), (4484, '流泉之众'),
      (4356, '悬木人'), (389, '烟谜主'), (2407, '沃陆之邦'), (1247, '那夏镇'),
      (2046, '至冬宫')]

s2p, s2o, raw = {}, {}, {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2o[sid] = re.search(r'\bowner\s*=\s*(\w+)', t).group(1)
    s2p[sid] = [int(x) for x in re.search(r'provinces = \{([^}]*)\}', t).group(1).split()]
    raw[sid] = t
p2s = {p: s for s, ps in s2p.items() for p in ps}

vp_state = collections.defaultdict(list)
print('=== 13 个 VP 省归属 ===')
for pid, cn in VP:
    s = p2s.get(pid)
    print(f'  省 {pid:5d} {cn:8s} -> state {s} owner {s2o.get(s)}')
    assert s, f'省 {pid} 不在任何州'
    vp_state[s].append((pid, 25))

# 冲突检查：目标州已有 VP？
for s in sorted(vp_state):
    t = raw[s]
    m = re.search(r'victory_points = \{([^}]*)\}', t)
    if m:
        print(f'  !! state {s} 已有 VP 行: {m.group(1)} —— 将被替换')
# 同国多请求
cap_cnt = collections.Counter(s2o[s] for s in vp_state)
conf = {k: v for k, v in cap_cnt.items() if v > 1}
print(f'同国多 capital 请求: {conf if conf else "无"}')

bdir = os.path.join(ROOT, '.backups', 'vp_add_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)


def set_vps_line(t, vps):
    line = ('victory_points = { ' + ' '.join(f'{p} {v}' for p, v in sorted(vps)) + ' }') if vps else None
    if re.search(r'victory_points = \{[^}]*\}', t):
        return re.sub(r'victory_points = \{[^}]*\}', line, t) if line else \
            re.sub(r'\r\n\t\tvictory_points = \{[^}]*\}', '', t)
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


for sid in sorted(vp_state):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = set_vps_line(raw[sid], vp_state[sid])
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)
print(f'VP 写入 {len(vp_state)} 个州，备份 {bdir}')

# ---- set_capital ----
for sid in sorted(vp_state):
    tag = s2o[sid]
    cdir = next(f for f in os.listdir(CD) if f.upper().startswith(tag))
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
target = next((f for f in os.listdir(LOC) if 'victory' in f.lower() and f.endswith('.yml')),
              'DOT_Victory_Points_gamma_l_simp_chinese.yml')
lp = os.path.join(LOC, target)
cur = open(lp, encoding='utf-8-sig', errors='replace').read() if os.path.exists(lp) else ''
missing = [(pid, cn) for pid, cn in VP if f'VICTORY_POINTS_{pid}:' not in cur]
if missing:
    if not os.path.exists(lp):
        open(lp, 'wb').write(b'\xef\xbb\xbfl_simp_chinese:\r\n')
        cur = 'l_simp_chinese:\r\n'
    add = '\r\n'.join(f' VICTORY_POINTS_{pid}:0 "{cn}"' for pid, cn in missing)
    with open(lp, 'wb') as fh:
        fh.write((cur.rstrip('\r\n') + '\r\n' + add + '\r\n').encode('utf-8'))
    print(f'本地化：{target} 追加 {len(missing)} 条')

# ---- 复验 ----
tot, errs = 0, 0
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    for m in re.finditer(r'victory_points = \{([^}]*)\}', t):
        v = m.group(1).split()
        tot += 1
        if len(v) != 2 or not v[1].isdigit():
            errs += 1
print(f'复验：全 mod VP {tot} 个，格式异常 {errs}')
for pid, cn in VP:
    s = p2s[pid]
    t = open(os.path.join(ST, f'{s}-State_{s}.txt'), encoding='utf-8-sig', newline='').read()
    m = re.search(r'victory_points = \{([^}]*)\}', t)
    ok = m and f'{pid} 25' in m.group(1)
    print(f'  省 {pid} {cn}: state {s} {"✓" if ok else "✗"}')

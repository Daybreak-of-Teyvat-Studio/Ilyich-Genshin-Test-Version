# -*- coding: utf-8 -*-
"""apply_batch_1005.py —— 10-05 批次：转省 2192→722 + 州名 15 + VP 7，落地后逐条回读验证

格式规矩：括号=VP（省号,名,数值）；无括号=state（州号,名）。
"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
NAMES_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VP_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
BP = os.path.join(MOD, 'map', 'buildings.txt')

TRANSFER = (2192, 707, 722)          # (省, 旧州, 新州)
NAMES = [(735, '漫曛谷'), (765, '焚风试炼处'), (722, '荧草窟'), (817, '沃陆之邦'),
         (809, '【石火坠陨处】'), (830, '孑遗的留迹'), (804, '觐山古道'),
         (803, '流火的实验地'), (837, '天火之冠'), (81, '刺梨岩'), (552, '呼呼丘'),
         (558, '彩彩崖'), (603, '悠悠集市'), (550, '浪浪湾'), (526, '提提岛')]
VPS = [(606, '谜土祭祀场', 15), (4310, '茜特菈莉的住处', 15), (1492, '飞行试炼场', 15),
       (1137, '远古圣山', 25), (917, '卡萨扎莱宫', 15), (1739, '天火之冠', 15),
       (795, '隐匿的谜土', 15)]


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


# ---------- 1. 转省 2192: 707 → 722（含 buildings 第 1 列同步） ----------
pid, src, dst = TRANSFER
for sid in (src, dst):
    p = os.path.join(ST, f'{sid}-State_{sid}.txt')
    raw, t = load(p)
    pm = re.search(r'(provinces\s*=\s*\{)([^}]*)(\})', t)
    provs = pm.group(2).split()
    if sid == src:
        assert str(pid) in provs, f'p{pid} 不在 s{src}'
        provs.remove(str(pid))
    else:
        assert str(pid) not in provs, f'p{pid} 已在 s{dst}'
        provs.append(str(pid))
    t = t[:pm.start()] + pm.group(1) + '\r\n\t\t' + ' '.join(provs) + '\r\n\t' + pm.group(3) + t[pm.end():]
    save(p, t, raw[:3] == b'\xef\xbb\xbf')
raw = open(BP, 'rb').read()
lines = raw.decode('utf-8-sig').split('\r\n')
nb = 0
for i, l in enumerate(lines):
    f = l.split(';')
    if len(f) == 7 and f[6] == str(pid) and f[0] == str(src):
        f[0] = str(dst)
        lines[i] = ';'.join(f)
        nb += 1
open(BP, 'wb').write('\r\n'.join(lines).encode('utf-8'))
print(f'转省 p{pid}: s{src}→s{dst}，buildings 同步 {nb} 条')

# ---------- 2. 州名 15 ----------
raw, t = load(NAMES_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
nm_map = dict(NAMES)
out, n_ok, warns = [], 0, []
seen = set()
for l in t.split(nl):
    m = re.match(r'^(\s*DOT_STATE_(\d+):)0?(\s*)"([^"]*)"', l)
    if m:
        sid = int(m.group(2))
        if sid in nm_map and sid not in seen:
            seen.add(sid)
            cur = m.group(4)
            want = nm_map[sid]
            if cur == want:
                n_ok += 1          # 已是目标名
            elif cur == '*':
                l = f'{m.group(1)}0{m.group(3)}"{want}"'
                n_ok += 1
            else:
                warns.append(f's{sid} 现名「{cur}」≠ 目标「{want}」，未动')
    out.append(l)
save(NAMES_F, nl.join(out), has_bom)
print(f'州名: 写入/确认 {n_ok}/15' + (f'；⚠ ' + '；'.join(warns) if warns else ''))

# ---------- 3. VP 7（值 + 本地化） ----------
p2s = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        p2s[int(x)] = sid

for vpid, nm, val in VPS:
    h = p2s.get(vpid)
    assert h, f'p{vpid} 不在任何州'
    p = os.path.join(ST, f'{h}-State_{h}.txt')
    raw, t = load(p)
    cur = vps_of(t).get(vpid)
    if cur == val:
        print(f'  VP p{vpid}「{nm}」{val}: s{h} 已有 ✓')
    elif cur is None:
        ls = t.rfind('\n', 0, history_close(t)) + 1
        ins = f'\t\tvictory_points = {{ {vpid} {val} }}\r\n'
        t = t[:ls] + ins + t[ls:]
        save(p, t, raw[:3] == b'\xef\xbb\xbf')
        print(f'  VP p{vpid}「{nm}」{val}: 写入 s{h} ✓')
    else:
        print(f'  VP p{vpid}: s{h} 现值 {cur} ≠ {val}，未动 ⚠')

raw, t = load(VP_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
lines = t.split(nl)
have = {int(m.group(1)): m.group(2) for l in lines if (m := re.match(r'^\s*VICTORY_POINTS_(\d+):\d*\s+"([^"]*)"', l))}
out = list(lines)
n_add = 0
for pid, nm, _ in VPS:
    if pid in have:
        if have[pid] != nm:
            print(f'  ⚠ VICTORY_POINTS_{pid} 现为「{have[pid]}」≠「{nm}」，未动')
        continue
    out.append(f' VICTORY_POINTS_{pid}:0 "{nm}"')
    n_add += 1
save(VP_F, nl.join(out), has_bom)
print(f'VP 本地化: 加 {n_add} 条')

# ---------- 4. 回读验证 ----------
print()
print('=== 回读验证 ===')
errs = 0
for sid in (src, dst):
    t = open(os.path.join(ST, f'{sid}-State_{sid}.txt'), encoding='utf-8-sig').read()
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    has = str(pid) in pm.group(1).split()
    want = (sid == dst)
    errs += has != want
    print(f'  s{sid} 含 p{pid}: {has} {"✓" if has == want else "✗"}')
t = open(NAMES_F, encoding='utf-8-sig').read()
for sid, nm in NAMES:
    ok = re.search(rf'DOT_STATE_{sid}:0\s*"{re.escape(nm)}"', t) is not None
    errs += not ok
    if not ok:
        print(f'  ✗ s{sid}「{nm}」验证失败')
for pid2, nm, val in VPS:
    h = p2s[pid2]
    t = open(os.path.join(ST, f'{h}-State_{h}.txt'), encoding='utf-8-sig').read()
    ok = vps_of(t).get(pid2) == val
    t2 = open(VP_F, encoding='utf-8-sig').read()
    ok = ok and re.search(rf'VICTORY_POINTS_{pid2}:0\s*"{re.escape(nm)}"', t2) is not None
    errs += not ok
    if not ok:
        print(f'  ✗ VP p{pid2}「{nm}」{val} 验证失败')
print('全部通过 ✓' if errs == 0 else f'{errs} 项验证失败 ✗')

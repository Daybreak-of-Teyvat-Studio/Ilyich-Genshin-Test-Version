# -*- coding: utf-8 -*-
"""fix_4135.py —— 纠正 4315 笔误：4315* 清除（含连带 SGD 首都恢复 393）、4135 曜石图腾柱·花羽会（25，首都）"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
VP_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'fix4135_{stamp}')
os.makedirs(BD, exist_ok=True)


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


# 1. 清除 p4315（s755）
p = os.path.join(ST, '755-State_755.txt')
shutil.copy2(p, BD)
raw, t = load(p)
t, n = re.subn(r'[ \t]*victory_points\s*=\s*\{\s*4315\s+\d+\s*\}[ \t]*\r?\n?', '', t)
save(p, t, raw[:3] == b'\xef\xbb\xbf')
print(f's755 删 p4315 条目 ×{n}')

# 2. 加 p4135（s692）
p = os.path.join(ST, '692-State_692.txt')
shutil.copy2(p, BD)
raw, t = load(p)
assert 4135 not in vps_of(t), 's692 已有 p4135'
ls = t.rfind('\n', 0, history_close(t)) + 1
t = t[:ls] + '\t\tvictory_points = { 4135 25 }\r\n' + t[ls:]
save(p, t, raw[:3] == b'\xef\xbb\xbf')
print('s692 加 p4135=25')

# 3. 本地化：删 4315，加 4135
shutil.copy2(VP_F, BD)
raw, t = load(VP_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
out = []
for l in t.split(nl):
    if re.match(r'^\s*VICTORY_POINTS_4315:', l):
        continue
    out.append(l)
out.append(' VICTORY_POINTS_4135:0 "曜石图腾柱·花羽会"')
save(VP_F, nl.join(out), has_bom)
print('本地化: 删 VICTORY_POINTS_4315，加 4135')

# 4. 首都：NFF=692；SGD 恢复 393
for tag, sid in (('NFF', 692), ('SGD', 393)):
    hits = glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag}*.txt'))
    p = hits[0]
    shutil.copy2(p, BD)
    raw, t = load(p)
    t2, n = re.subn(r'(?m)^(\s*capital\s*=\s*)\d+', rf'\g<1>{sid}', t, count=1)
    save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'{tag} capital = {sid}')

# 5. 回读验证
print()
print('=== 回读验证 ===')
errs = 0
t = open(os.path.join(ST, '755-State_755.txt'), encoding='utf-8-sig').read()
ok = 4315 not in vps_of(t)
print(f's755 无 p4315: {"✓" if ok else "✗"}')
errs += not ok
t = open(os.path.join(ST, '692-State_692.txt'), encoding='utf-8-sig').read()
ok = vps_of(t).get(4135) == 25
print(f's692 p4135=25: {"✓" if ok else "✗"}')
errs += not ok
t = open(VP_F, encoding='utf-8-sig').read()
ok = 'VICTORY_POINTS_4315:' not in t and re.search(r'VICTORY_POINTS_4135:0\s*"曜石图腾柱·花羽会"', t)
print(f'本地化 4315 删 / 4135 加: {"✓" if ok else "✗"}')
errs += not ok
for tag, sid in (('NFF', 692), ('SGD', 393)):
    t = open(glob.glob(os.path.join(MOD, 'history', 'countries', f'{tag}*.txt'))[0],
             encoding='utf-8-sig').read()
    m = re.search(r'(?m)^\s*capital\s*=\s*(\d+)', t)
    ok = m and int(m.group(1)) == sid
    print(f'{tag} capital={sid}: {"✓" if ok else "✗ 现为 " + (m.group(1) if m else "无")}')
    errs += not ok
print('\n全部通过 ✓' if errs == 0 else f'\n{errs} 项失败 ✗')

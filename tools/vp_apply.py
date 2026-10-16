# -*- coding: utf-8 -*-
"""蒙德 VP 批次 + 马斯克海→马斯克礁 改名：备份 → 应用 → 验证（双副本）"""
import os, io, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'vp_mond_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []

ENTRIES = [
    (908, '风起地神像', 20), (3643, '鹰之门', 15), (352, '无相之雷', 20), (1306, '南风之狮的庙宇', 15),
    (1252, '西风之鹰的庙宇', 15), (3588, '忘却之峡', 15), (1535, '铭记之谷', 15), (473, '晨曦酒庄', 25),
    (3539, '苍风高地神像', 20), (733, '塞西莉亚苗圃', 15), (1334, '无相之风', 20), (288, '仲夏庭园', 15),
    (3383, '风龙废墟神像', 20), (3515, '急冻树', 20), (2273, '北风之狼的庙宇', 15), (3433, '西风大教堂', 25),
    (3456, '蒙德城风神像', 50), (1395, '蒙德大桥', 15), (292, '喷泉广场', 10), (3481, '西风骑士团总部', 50),
    (3441, '天使的馈赠', 15), (3485, '舒茨铁铺', 10), (1960, '阿卡狄亚遗迹', 15), (1930, '风车镇', 25),
    (3296, '风息山神像', 20), (1560, '山风的荆冕', 15), (919, '西风骑士团遗迹', 10), (3223, '疗养院旧址', 15),
    (1582, '守望者·堕天', 20), (2294, '宗室密藏之地', 10),
]
EXISTING_EDIT = {292: 10}   # p292 已有 { 292 25 } → 改 10

# ---------- 备份 ----------
for label, root in [('repo', G), ('depl', DEPL)]:
    shutil.copytree(os.path.join(root, 'history', 'states'), os.path.join(BD, f'{label}_states'))
shutil.copy2(os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml'), os.path.join(BD, 'repo_DOT_Victory_Points.yml'))
shutil.copy2(os.path.join(G, 'localisation', 'simp_chinese', 'victory_points_l_simp_chinese.yml'), os.path.join(BD, 'repo_victory_points_l.yml'))
shutil.copy2(os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Strategic_Region_Names_l_simp_chinese.yml'), os.path.join(BD, 'repo_RegionNames.yml'))
shutil.copy2(os.path.join(DEPL, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml'), os.path.join(BD, 'depl_DOT_Victory_Points.yml'))
shutil.copy2(os.path.join(DEPL, 'localisation', 'simp_chinese', 'victory_points_l_simp_chinese.yml'), os.path.join(BD, 'depl_victory_points_l.yml'))
shutil.copy2(os.path.join(DEPL, 'localisation', 'simp_chinese', 'DOT_Strategic_Region_Names_l_simp_chinese.yml'), os.path.join(BD, 'depl_RegionNames.yml'))
o.append(f'备份: {BD}')

# ---------- 省→州 映射 ----------
sd = os.path.join(G, 'history', 'states')
p2s = {}
sfiles = {}
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    sfiles[sid] = f
    for p in m.group(1).split():
        p2s[int(p)] = sid

by_state = {}
for pid, name, val in ENTRIES:
    by_state.setdefault(p2s[pid], []).append((pid, name, val))

# ---------- 改州文件 ----------
def find_buildings_end(t):
    i = t.find('buildings = {')
    if i < 0:
        return -1
    j = t.find('{', i)
    depth = 0
    k = j
    while k < len(t):
        if t[k] == '{':
            depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    return -1

for label, root in [('仓库', G), ('副本', DEPL)]:
    for sid, items in sorted(by_state.items()):
        fp = os.path.join(root, 'history', 'states', sfiles[sid])
        raw = io.open(fp, 'rb').read()
        bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
        t = raw.decode('utf-8-sig')
        nl = '\r\n' if b'\r\n' in raw else '\n'
        changed = []

        # (a) 编辑既有值（p292）
        for pid, name, val in items:
            if pid in EXISTING_EDIT:
                pat = re.compile(r'(victory_points\s*=\s*\{\s*' + str(pid) + r'\s+)\d+(\s*\})')
                t2, n = pat.subn(r'\g<1>' + str(val) + r'\g<2>', t)
                if n:
                    t = t2
                    changed.append(f'编辑 p{pid} 值→{val}')

        # (b) 追加新块
        add = [(pid, name, val) for pid, name, val in items if pid not in EXISTING_EDIT]
        if add:
            vps = list(re.finditer(r'victory_points\s*=\s*\{[^}]*\}', t))
            blocks = ''.join(f'\t\tvictory_points = {{ {pid} {val} }}{nl}' for pid, name, val in add)
            if vps:
                pos = vps[-1].end()
                if t[pos:pos+len(nl)] == nl:
                    pos += len(nl)
                # 行尾插入
                t = t[:pos] + blocks + t[pos:]
            else:
                be = find_buildings_end(t)
                if be < 0:
                    o.append(f'  ✗ 州{sid}: 找不到 buildings 块结尾，跳过！')
                    continue
                if t[be:be+len(nl)] == nl:
                    be += len(nl)
                t = t[:be] + blocks + t[be:]
            changed.append(f'追加 {[(p, v) for p, n2, v in add]}')

        io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t.encode('utf-8'))
        o.append(f'{label} 州{sid} ({sfiles[sid]}): ' + '; '.join(changed))

# ---------- loc ----------
o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    # (1) DOT_Victory_Points：追加新键 + 改 292
    fp = os.path.join(root, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    t = raw.decode('utf-8-sig')
    nl = '\r\n'
    # 改 292 文本
    t2, n292 = re.subn(r'(VICTORY_POINTS_292:\d*\s*")[^"]*(")', r'\g<1>喷泉广场\g<2>', t)
    t = t2
    # 追加其余 29 个（292 除外）
    lines = []
    for pid, name, val in ENTRIES:
        if pid == 292:
            continue
        if f'VICTORY_POINTS_{pid}:' in t:
            o.append(f'  ⚠ {label}: VICTORY_POINTS_{pid} 已存在，跳过追加')
            continue
        lines.append(f'VICTORY_POINTS_{pid}:0 "{name}"')
    if lines:
        body = t.rstrip('\r\n') + nl + nl.join(lines)
        t = body
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t.encode('utf-8'))
    o.append(f'{label} DOT_Victory_Points: 292→喷泉广场({n292}), 追加 {len(lines)} 键')

    # (2) victory_points_l：352 旧键对齐为 无相之雷
    fp = os.path.join(root, 'localisation', 'simp_chinese', 'victory_points_l_simp_chinese.yml')
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    t = raw.decode('utf-8-sig')
    t2, n352 = re.subn(r'(VICTORY_POINTS_352:\d*\s*")[^"]*(")', r'\g<1>无相之雷\g<2>', t)
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t2.encode('utf-8'))
    o.append(f'{label} victory_points_l: 352 → 无相之雷 ({n352} 处)')

    # (3) 马斯克海 → 马斯克礁
    fp = os.path.join(root, 'localisation', 'simp_chinese', 'DOT_Strategic_Region_Names_l_simp_chinese.yml')
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    t = raw.decode('utf-8-sig')
    t2, nren = re.subn('马斯克海', '马斯克礁', t)
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t2.encode('utf-8'))
    o.append(f'{label} 战略区名: 马斯克海→马斯克礁 ({nren} 处)')

# ---------- 验证 ----------
o.append('')
o.append('===== 验证（仓库） =====')
for sid, items in sorted(by_state.items()):
    t = io.open(os.path.join(sd, sfiles[sid]), 'rb').read().decode('utf-8-sig')
    blocks = re.findall(r'victory_points\s*=\s*\{([^}]*)\}', t)
    pairs = []
    for b in blocks:
        toks = b.split()
        for i in range(0, len(toks) - 1, 2):
            pairs.append((int(toks[i]), int(toks[i+1])))
    want = [(pid, val) for pid, name, val in items]
    got = [pr for pr in pairs if pr[0] in [w[0] for w in want]]
    ok = sorted(got) == sorted(want)
    braces = t.count('{') == t.count('}')
    o.append(f'  州{sid}: 新VP核对={"✓" if ok else "✗ " + str(got)} 括号={"✓" if braces else "✗"} 全部块={pairs}')

io.open(os.path.join(REPO, 'tools', 'vp_apply_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('DONE')
print('\n'.join(o[-25:]))

# -*- coding: utf-8 -*-
import os, io, re, sys, shutil, datetime, hashlib
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'vp2_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []

ENTRIES = [
    (1506, '疗养院旧址', 30), (3223, '疗养院风神像', 25), (1451, '好肉族大锅', 5), (748, '黑日族方碑', 5),
    (3657, '好睡族大殿', 5), (301, '野猪林', 5), (3349, '导光机关', 5), (894, '导光机关', 5),
]
EDIT_EXISTING = {3223: (25, '疗养院风神像')}

# 备份：涉及的州文件 + loc
STATES = [392, 427, 433, 448, 511, 522]
for label, root in [('repo', G), ('depl', DEPL)]:
    for sid in STATES:
        shutil.copy2(os.path.join(root, 'history', 'states', f'{sid}-State_{sid}.txt'), os.path.join(BD, f'{label}_{sid}.txt'))
    shutil.copy2(os.path.join(root, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml'), os.path.join(BD, f'{label}_DOT_VP.yml'))
o.append(f'备份: {BD}')

sd = os.path.join(G, 'history', 'states')
p2s = {}
sfiles = {}
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    sfiles[sid] = f
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    for p in m.group(1).split():
        p2s[int(p)] = sid

by_state = {}
for pid, name, val in ENTRIES:
    by_state.setdefault(p2s[pid], []).append((pid, name, val))

def buildings_end(t):
    i = t.find('buildings = {')
    if i < 0:
        return -1
    j = t.find('{', i); depth = 0; k = j
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
        msgs = []
        for pid, name, val in items:
            if pid in EDIT_EXISTING:
                nv, nn = EDIT_EXISTING[pid]
                pat = re.compile(r'(victory_points\s*=\s*\{\s*' + str(pid) + r'\s+)\d+(\s*\})')
                t, n = pat.subn(r'\g<1>' + str(nv) + r'\g<2>', t)
                if n:
                    msgs.append(f'改 p{pid}→{nv}')
        add = [(p, n2, v) for p, n2, v in items if p not in EDIT_EXISTING]
        if add:
            vps = list(re.finditer(r'victory_points\s*=\s*\{[^}]*\}', t))
            blocks = ''.join(f'\t\tvictory_points = {{ {p} {v} }}{nl}' for p, n2, v in add)
            if vps:
                pos = vps[-1].end()
                if t[pos:pos + len(nl)] == nl:
                    pos += len(nl)
                t = t[:pos] + blocks + t[pos:]
            else:
                be = buildings_end(t)
                if be < 0:
                    msgs.append('✗ 无 buildings 块')
                    continue
                if t[be:be + len(nl)] == nl:
                    be += len(nl)
                t = t[:be] + blocks + t[be:]
            msgs.append(f'追加 {[(p, v) for p, n2, v in add]}')
        io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t.encode('utf-8'))
        o.append(f'{label} 州{sid}: ' + '; '.join(msgs))

# loc
o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    t = raw.decode('utf-8-sig')
    t, n3223 = re.subn(r'(VICTORY_POINTS_3223:\d*\s*")[^"]*(")', r'\g<1>疗养院风神像\g<2>', t)
    lines = []
    for pid, name, val in ENTRIES:
        if pid in EDIT_EXISTING:
            continue
        if f'VICTORY_POINTS_{pid}:' in t:
            o.append(f'  ⚠ {label} {pid} 已存在，跳过')
            continue
        lines.append(f'VICTORY_POINTS_{pid}:0 "{name}"')
    if lines:
        t = t.rstrip('\r\n') + '\r\n' + '\r\n'.join(lines)
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t.encode('utf-8'))
    o.append(f'{label} loc: 3223→疗养院风神像({n3223}), 追加 {len(lines)} 键')

# 验证
o.append('')
o.append('===== 验证（双副本一致 + VP 核对） =====')
for sid, items in sorted(by_state.items()):
    fa = os.path.join(G, 'history', 'states', sfiles[sid])
    fb = os.path.join(DEPL, 'history', 'states', sfiles[sid])
    same = hashlib.md5(io.open(fa, 'rb').read()).digest() == hashlib.md5(io.open(fb, 'rb').read()).digest()
    t = io.open(fa, 'rb').read().decode('utf-8-sig')
    pairs = []
    for b in re.findall(r'victory_points\s*=\s*\{([^}]*)\}', t):
        tk = b.split()
        for i in range(0, len(tk) - 1, 2):
            pairs.append((int(tk[i]), int(tk[i + 1])))
    want = [(p, (EDIT_EXISTING[p][0] if p in EDIT_EXISTING else v)) for p, n2, v in items]
    got = [pr for pr in pairs if pr[0] in [w[0] for w in want]]
    o.append(f'  州{sid}: 核对={"✓" if sorted(got) == sorted(want) else "✗" + str(got)} 括号={"✓" if t.count("{") == t.count("}") else "✗"} 双副本一致={same} 全部块={pairs}')
a = io.open(os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml'), 'rb').read()
b = io.open(os.path.join(DEPL, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml'), 'rb').read()
o.append(f'  loc 双副本一致={a == b} BOM={a[:3] == bytes([0xef,0xbb,0xbf])} CRCRLF={a.count(bytes([13,13,10]))}')
tt = a.decode('utf-8-sig')
for k in ('VICTORY_POINTS_3223', 'VICTORY_POINTS_1506', 'VICTORY_POINTS_894'):
    for l in tt.splitlines():
        if k + ':' in l:
            o.append('    ' + l.strip()[:90])
io.open(os.path.join(REPO, 'tools', 'vp2_apply_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

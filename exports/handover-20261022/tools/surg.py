# -*- coding: utf-8 -*-
"""转省 + 合并 + 补号（州文件层）——干净版"""
import os, io, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'surg_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []
for label, root in [('repo', G), ('depl', DEPL)]:
    shutil.copytree(os.path.join(root, 'history', 'states'), os.path.join(BD, f'{label}_states'))
o.append(f'备份: {BD}')

def sdir(root):
    return os.path.join(root, 'history', 'states')

def load(root, sid):
    fp = os.path.join(sdir(root), f'{sid}-State_{sid}.txt')
    if not os.path.exists(fp):
        return None, None
    raw = io.open(fp, 'rb').read()
    return fp, raw.decode('utf-8-sig')

def get_provs(t):
    m = re.search(r'(provinces\s*=\s*\{)(\s*)([^}]*)(\s*)(\})', t, re.S)
    return [int(x) for x in m.group(3).split()]

def set_provs(t, plist):
    m = re.search(r'(provinces\s*=\s*\{)(\s*)([^}]*)(\s*)(\})', t, re.S)
    return t[:m.start(3)] + ' '.join(str(p) for p in plist) + t[m.end(3):]

def take_assets(t, prov):
    vps = ''
    for m in list(re.finditer(r'(?m)^\t*victory_points\s*=\s*\{\s*' + str(prov) + r'\s+(\d+)\s*\}\r?\n', t)):
        vps += f'\t\tvictory_points = {{ {prov} {m.group(1)} }}\r\n'
        t = t[:m.start()] + t[m.end():]
    blk = ''
    bm = re.search(r'(?m)^\t+' + str(prov) + r'\s*=\s*\{', t)
    if bm:
        k = bm.end() - 1
        depth = 0
        while k < len(t):
            if t[k] == '{':
                depth += 1
            elif t[k] == '}':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        le = k + 1
        while le < len(t) and t[le] in '\r\n':
            le += 1
        blk = t[bm.start():le]
        t = t[:bm.start()] + t[le:]
    return t, vps, blk

def buildings_close(t):
    bi = t.find('buildings = {')
    k = t.find('{', bi)
    depth = 0
    while k < len(t):
        if t[k] == '{':
            depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return -1

def add_assets(t, vps, blk):
    if vps:
        vpms = list(re.finditer(r'victory_points\s*=\s*\{[^}]*\}', t))
        if vpms:
            pos = vpms[-1].end()
            while pos < len(t) and t[pos] in '\r\n':
                pos += 1
            t = t[:pos] + vps + t[pos:]
        else:
            k = buildings_close(t)
            pos = t.find('\n', k) + 1
            t = t[:pos] + vps + t[pos:]
    if blk:
        k = buildings_close(t)
        ls = t.rfind('\n', 0, k) + 1
        t = t[:ls] + blk + t[ls:]
    return t

MOVE = {1570: 484, 1306: 435, 1960: 435, 3515: 435, 845: 500}
MERGE_INTO = {510: [511, 522]}
RENAME = {702: 511, 701: 522}

for label, root in [('仓库', G), ('副本', DEPL)]:
    o.append(f'===== {label} =====')
    # A 转省
    for prov, tgt in MOVE.items():
        src = None
        for sid in range(1, 703):
            fp, t = load(root, sid)
            if t is None:
                continue
            if prov in get_provs(t):
                src = (sid, fp, t)
                break
        sid, fp, t = src
        t, vps, blk = take_assets(t, prov)
        t = set_provs(t, [p for p in get_provs(t) if p != prov])
        io.open(fp, 'wb').write(t.encode('utf-8'))
        tfp, tt = load(root, tgt)
        tt = set_provs(tt, sorted(set(get_provs(tt)) | {prov}))
        tt = add_assets(tt, vps, blk)
        io.open(tfp, 'wb').write(tt.encode('utf-8'))
        o.append(f'  转省 p{prov}: {sid} → {tgt} (VP={bool(vps)}, 块={bool(blk)})')

    # B 合并
    for survivor, absorbed in MERGE_INTO.items():
        fp, t = load(root, survivor)
        allp = list(get_provs(t))
        for a in absorbed:
            afp, at = load(root, a)
            ap = get_provs(at)
            allp += ap
            for p in ap:
                at, vps, blk = take_assets(at, p)
                t = add_assets(t, vps, blk)
            os.remove(afp)
        t = set_provs(t, sorted(set(allp)))
        io.open(fp, 'wb').write(t.encode('utf-8'))
        o.append(f'  合并 {survivor} ← {absorbed}: 共 {len(sorted(set(allp)))} 省')

    # C 补号
    for old, new in RENAME.items():
        fp, t = load(root, old)
        t = re.sub(r'(\bid\s*=\s*)' + str(old) + r'\b', r'\g<1>' + str(new), t, count=1)
        t = re.sub(r'name\s*=\s*"DOT_STATE_' + str(old) + r'"[^\r\n]*', f'name="DOT_STATE_{new}" # name="STATE_{old}"', t, count=1)
        nfp = os.path.join(sdir(root), f'{new}-State_{new}.txt')
        io.open(nfp, 'wb').write(t.encode('utf-8'))
        os.remove(fp)
        o.append(f'  补号 {old} → {new}: {len(get_provs(t))} 省')

o.append('')
o.append('===== 验证 =====')
for label, root in [('仓库', G), ('副本', DEPL)]:
    ids = sorted(int(f.split('-')[0]) for f in os.listdir(sdir(root)) if f.endswith('.txt'))
    o.append(f'  {label}: {len(ids)} 州, 连号={ids == list(range(1, len(ids) + 1))}, 缺={[i for i in range(1, max(ids) + 1) if i not in set(ids)]}')
    p2s = {}
    for sid in ids:
        fp, t = load(root, sid)
        for p in get_provs(t):
            p2s.setdefault(p, []).append(sid)
    o.append(f'    重复归属: { {p: s for p, s in p2s.items() if len(s) > 1} or "无 ✓"}')
    for prov, tgt in MOVE.items():
        o.append(f'    p{prov} 属州={p2s.get(prov)} 应[{tgt}]')
    for s in (510, 435, 484, 500, 511, 522):
        fp, t = load(root, s)
        if t is None:
            o.append(f'    州{s} 不存在!!')
            continue
        o.append(f'    州{s}: 省{len(get_provs(t))}个, VP={re.findall(r"victory_points = {[^}]*}", t)}, 括号 {t.count(chr(123))}=={t.count(chr(125))}')
io.open(os.path.join(REPO, 'tools', 'surg_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

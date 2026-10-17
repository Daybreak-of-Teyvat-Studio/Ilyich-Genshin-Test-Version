# -*- coding: utf-8 -*-
"""引用同步：合并 511/522→510；补号 701/702→522/511"""
import os, io, re, sys, shutil, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
o = []

# 映射：旧号 → 新号（用于引用替换）
MAP = {}     # 511/522 → 510
for a in (511, 522):
    MAP[a] = 510
REN = {701: 522, 702: 511}

# ---- 1) airports / rocketsites ----
for label, root in [('仓库', G), ('副本', DEPL)]:
    for fname in ('airports.txt', 'rocketsites.txt'):
        fp = os.path.join(root, 'map', fname)
        raw = io.open(fp, 'rb').read()
        t = raw.decode('utf-8-sig')
        vals = {}
        for m in re.finditer(r'(?m)^(\d+)\s*=\s*(.*)$', t):
            vals[int(m.group(1))] = m.group(2).strip()
        # 记录 701/702 的值
        v701, v702 = vals.get(701, ''), vals.get(702, '')
        # 删除键 511/522/701/702
        lines = [l for l in t.splitlines() if not re.match(r'\s*(511|522|701|702)\s*=', l)]
        # 写回：701 的值 → 键 522；702 的值 → 键 511
        lines.append(f'522={v701}')
        lines.append(f'511={v702}')
        io.open(fp, 'wb').write(('\r\n'.join(lines) + '\r\n').encode('utf-8'))
        chk = io.open(fp, 'rb').read().decode('utf-8-sig')
        o.append(f'{label} {fname}: 键 522={v701!r}, 511={v702!r}; 行数={len(chk.splitlines())}')

# ---- 2) loc：DOT_STATE_701/702 → 522/511 ----
LOCF = 'localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml'
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, LOCF.replace('/', os.sep))
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    t = raw.decode('utf-8-sig')
    # 取 701/702 的值
    def val(t, sid):
        m = re.search(r'(?m)^\s*DOT_STATE_' + str(sid) + r':\d*\s*"([^"]*)"', t)
        return m.group(1) if m else None
    v701 = val(t, 701)
    v702 = val(t, 702)
    o.append(f'{label} loc 原 701={v701!r}, 702={v702!r}')
    # 511/522 的旧值（合并州名，将被覆盖）
    o.append(f'   合并州名 510={val(t,510)!r} 511={val(t,511)!r} 522={val(t,522)!r}')
    # 覆盖式重映射：511 ← 702, 522 ← 701
    if v702 is not None:
        t = re.sub(r'(DOT_STATE_511:\d*\s*")[^"]*(")', lambda m: m.group(1) + v702 + m.group(2), t, count=1)
    if v701 is not None:
        t = re.sub(r'(DOT_STATE_522:\d*\s*")[^"]*(")', lambda m: m.group(1) + v701 + m.group(2), t, count=1)
    # 701/702 置 *
    for old in (701, 702):
        t = re.sub(r'(DOT_STATE_' + str(old) + r':\d*\s*")[^"]*(")', r'\g<1>*\g<2>', t, count=1)
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t.encode('utf-8'))
    for k in (510, 511, 522, 701, 702):
        for l in t.splitlines():
            if re.match(r'\s*DOT_STATE_' + str(k) + r':', l):
                o.append('   ' + l.strip()[:80])

# ---- 3) 首都：capital = 511/522 → 510；= 701/702 → 522/511 ----
o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    cdir = os.path.join(root, 'history', 'countries')
    for fp in glob.glob(os.path.join(cdir, '*.txt')):
        raw = io.open(fp, 'rb').read()
        t = raw.decode('utf-8-sig')
        m = re.search(r'(?m)^(\s*capital\s*=\s*)(\d+)', t)
        if m and int(m.group(2)) in (511, 522, 701, 702):
            old = int(m.group(2))
            new = MAP.get(old) or REN.get(old)
            t = t[:m.start(2)] + str(new) + t[m.end(2):]
            io.open(fp, 'wb').write(t.encode('utf-8'))
            o.append(f'  {label} {os.path.basename(fp)}: capital {old} → {new}')

# ---- 4) 脚本引用（token 模式） ----
o.append('')
PATTERNS = [
    (r'(owns_state\s*=\s*)', r''), (r'(controls_state\s*=\s*)', r''),
    (r'(has_full_control_of_state\s*=\s*)', r''), (r'(transfer_state\s*=\s*)', r''),
    (r'(?<![a-z_])state\s*=\s*', r''),
]
TOKENS = ['owns_state', 'controls_state', 'has_full_control_of_state', 'transfer_state']
DIRS = ['common', 'events', 'history', 'localisation', 'interface']
hits = []
for label, root in [('仓库', G), ('副本', DEPL)]:
    for d in DIRS:
        for fp in glob.glob(os.path.join(root, d, '**', '*.txt'), recursive=True) + \
                  glob.glob(os.path.join(root, d, '**', '*.yml'), recursive=True):
            if '.backups' in fp:
                continue
            raw = io.open(fp, 'rb').read()
            t = raw.decode('utf-8-sig', errors='replace')
            orig = t
            for sid_old, sid_new in list(MAP.items()) + list(REN.items()):
                for tok in TOKENS:
                    t = re.sub(r'(' + tok + r'\s*=\s*)' + str(sid_old) + r'(?![0-9])', r'\g<1>' + str(sid_new), t)
                t = re.sub(r'(\bstate\s*=\s*)' + str(sid_old) + r'(?![0-9])', r'\g<1>' + str(sid_new), t)
            if t != orig:
                io.open(fp, 'wb').write(t.encode('utf-8'))
                hits.append(os.path.relpath(fp, root))
                for l in t.splitlines():
                    if re.search(r'(owns_state|controls_state|has_full_control_of_state|transfer_state|state)\s*=\s*(510|511|522|701|702)\b', l):
                        o.append(f'  {label} {os.path.relpath(fp, root)}: {l.strip()[:120]}')
o.append(f'脚本引用改写文件数: {len(set(hits))}')
# 数字键州作用域块（人工复核）
o.append('')
o.append('===== 数字键块待人工复核（511/522/701/702 = {） =====')
for label, root in [('仓库', G)]:
    for d in ('common', 'events', 'history'):
        for fp in glob.glob(os.path.join(root, d, '**', '*.txt'), recursive=True):
            if '.backups' in fp:
                continue
            t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
            for i, l in enumerate(t.splitlines(), 1):
                if re.match(r'\s*(511|522|701|702)\s*=\s*\{', l):
                    o.append(f'  {os.path.relpath(fp, root)}:{i}: {l.strip()[:110]}')
io.open(os.path.join(REPO, 'tools', 'refsync_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

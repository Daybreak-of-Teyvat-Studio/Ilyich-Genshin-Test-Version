# -*- coding: utf-8 -*-
"""mega_fix_014.py —— 大修复包（DRY 默认，--apply 应用）
A) 昨晚补号残留：loc 四键 / airports+rocketsites 三键 / NCE 首都 / 奇观引用 94→86 / LYY transfer
B) ABY 合并：62+63+65+66+67→62（省/建筑/人力/资源相加；63/65/66/67 引用→62）
C) 补号：703/704/705/706 → 63/65/66/67（文件/id/name键/选址键/buildings行/引用）
D) 战略区：新建 id=46 马斯克海（合并62的5省+64的3省），从区域1移出
"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'mega014_{stamp}')
os.makedirs(BD, exist_ok=True)

def rd(p):
    raw = open(p, 'rb').read()
    return raw, raw.decode('utf-8-sig')

def wr(p, t, raw, tag):
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_{os.path.basename(p)}'))
        open(p, 'wb').write(t.encode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'))

def sub_exact(t, old, new, expect, tag, label):
    n = t.count(old)
    if n != expect:
        print(f'  ★ {tag} {label}: "{old[:44]}" ×{n}（预期 {expect}）跳过')
        return t, False
    print(f'  {tag} {label}: ×{n} ✓' + ('' if APPLY else '(DRY)'))
    return t.replace(old, new), True

def sub_re(t, pat, repl, expect, tag, label):
    rx = re.compile(pat)
    n = len(rx.findall(t))
    if n != expect:
        print(f'  ★ {tag} {label}: 匹配 {n}（预期 {expect}）跳过')
        return t, False
    print(f'  {tag} {label}: ×{n} ✓' + ('' if APPLY else '(DRY)'))
    return rx.sub(repl, t), True

# ================= A) 昨晚残留 =================
print('=== A) 昨晚补号残留 ===')
LOC = os.path.join('localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
for tag, base in COPIES:
    p = os.path.join(base, LOC)
    raw, t = rd(p)
    t, _ = sub_exact(t, 'DOT_STATE_90:0 "*"', 'DOT_STATE_90:0 "分道誓约之地"', 1, tag, 'loc90')
    t, _ = sub_exact(t, 'DOT_STATE_89:0 "*"', 'DOT_STATE_89:0 "回声之子"', 1, tag, 'loc89')
    t, _ = sub_exact(t, 'DOT_STATE_708:00 "分道誓约之地"', 'DOT_STATE_708:00 "*"', 1, tag, 'loc708')
    t, _ = sub_exact(t, 'DOT_STATE_709:0 "回声之子"', 'DOT_STATE_709:0 "*"', 1, tag, 'loc709')
    wr(p, t, raw, tag)

    # airports / rocketsites：89←321, 90←2365, 94←1289（值随州搬）；删 707/708/709 键
    for fname, targets in (('airports.txt', {'89': '321', '90': '2365', '94': '1289'}),
                           ('rocketsites.txt', {'89': '4186', '90': '4165', '94': '1289'})):
        p = os.path.join(base, 'map', fname)
        raw, t = rd(p)
        out = []
        for l in t.split('\n'):
            m = re.match(r'^(\s*)(\d+)(\s*=\s*\{)', l)
            if m:
                sid = m.group(2)
                if sid in ('707', '708', '709'):
                    print(f'  {tag} {fname}: 删键 s{sid}' + ('' if APPLY else '(DRY)'))
                    continue
                if sid in targets:
                    l = f'{sid}={{{targets[sid]} }}'
                    print(f'  {tag} {fname}: s{sid} 值改为 {targets[sid]} ✓' + ('' if APPLY else '(DRY)'))
            out.append(l)
        wr(p, '\n'.join(out), raw, tag)

    # NCE 首都
    p = os.path.join(base, 'history', 'countries', 'NCE - Children_of_Echoes.txt')
    raw, t = rd(p)
    t, _ = sub_exact(t, 'capital = 709', 'capital = 89', 1, tag, 'NCE首都')
    wr(p, t, raw, tag)

    # 奇观引用 94→86（两文件）
    p = os.path.join(base, 'common', 'scripted_localisation', 'DOT_wonder_state_scripted_localisation.txt')
    raw, t = rd(p)
    t, _ = sub_exact(t, 'state = 94.id', 'state = 86.id', 9, tag, '奇观loc94', )
    wr(p, t, raw, tag)
    p = os.path.join(base, 'common', 'scripted_triggers', 'NewMOT_scripted_triggers.txt')
    raw, t = rd(p)
    t, _ = sub_exact(t, 'state = 94.id', 'state = 86.id', 1, tag, 'NewMOT 94.id')
    wr(p, t, raw, tag)
    for rel, pairs in ((os.path.join('common', 'decisions', 'DOT_Wonder_decisions.txt'),
                        [('controls_state = 94', 'controls_state = 86', 1)]),
                       (os.path.join('common', 'decisions', 'categories', 'DOT_Wonder_decision_categories.txt'),
                        [('controls_state = 94', 'controls_state = 86', 1), ('state = 94', 'state = 86', 1)]),
                       (os.path.join('common', 'on_actions', 'DOT_wonder_state_array_on_actions.txt'),
                        [('94 = {', '86 = {', 1)])):
        p = os.path.join(base, rel)
        raw, t = rd(p)
        for old, new, e in pairs:
            t, _ = sub_exact(t, old, new, e, tag, os.path.basename(rel))
        wr(p, t, raw, tag)
    # LYY KQP transfer 90/94 → 86（行锚定，避开注释行）
    p = os.path.join(base, 'common', 'scripted_effects', 'LYY_scripted_effects.txt')
    raw, t = rd(p)
    t, _ = sub_re(t, r'(?m)^(\s*)transfer_state = 90([ \t]*\r?)$', r'\g<1>transfer_state = 86\g<2>', 1, tag, 'LYY90')
    t, _ = sub_re(t, r'(?m)^(\s*)transfer_state = 94([ \t]*\r?)$', r'\g<1>transfer_state = 86\g<2>', 1, tag, 'LYY94')
    wr(p, t, raw, tag)

# ================= B) ABY 合并 =================
print()
print('=== B) ABY 合并 62+63+65+66+67→62 ===')
MERGE_FILES = {'63': 'N', '65': 'N', '66': 'N', '67': 'N'}
REF_EDITS = [
    (os.path.join('common', 'decisions', 'DVA_decisions.txt'), '63'),
    (os.path.join('common', 'decisions', 'DOT_Resources.txt'), '66/67'),
    (os.path.join('common', 'national_focus', 'FAV_FocusTree_00.txt'), '63'),
    (os.path.join('common', 'national_focus', 'FAV_FocusTree_01.txt'), '63'),
    (os.path.join('common', 'national_focus', 'LAW_FocusTree_02.txt'), '63'),
    (os.path.join('common', 'national_focus', 'MOT_Focus_II.txt'), '63'),
    (os.path.join('common', 'national_focus', 'NewMOT_FocusTree_00.txt'), '63'),
    (os.path.join('common', 'national_focus', 'RAGv1_Focus.txt'), '63'),
    (os.path.join('common', 'scripted_effects', 'NAT_Neo_effects.txt'), '65'),
    (os.path.join('events', 'INA_Events.txt'), '65/66'),
]
for tag, base in COPIES:
    # 合并州文件：62 重写
    p62 = None
    for f in glob.glob(os.path.join(base, 'history', 'states', '62-State_62.txt')):
        p62 = f
    raw, t = rd(p62)
    provinces = []
    bsum = {}
    provblocks = {}
    man = 0
    res = {}
    for sids, fn in ((('62',), None), (('63',), None), (('65',), None), (('66',), None), (('67',), None)):
        sid = sids[0]
        fs = [x for x in glob.glob(os.path.join(base, 'history', 'states', f'{sid}-*.txt'))]
        if not fs:
            continue
        tt = open(fs[0], encoding='utf-8-sig', errors='replace').read()
        m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', tt)
        if m2:
            provinces += [int(x) for x in re.findall(r'\d+', m2.group(1))]
        mm = re.search(r'manpower\s*=\s*(\d+)', tt)
        if mm:
            man += int(mm.group(1))
        mb = re.search(r'buildings\s*=\s*\{', tt)
        if mb:
            depth, i = 0, mb.end() - 1
            while i < len(tt):
                if tt[i] == '{':
                    depth += 1
                elif tt[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            blk = tt[mb.end():i]
            for pm in re.finditer(r'(?m)^[ \t]*(\d+)[ \t]*=\s*\{([^}]*)\}[ \t]*$', blk):
                provblocks.setdefault(pm.group(1), pm.group(2).strip())
            blk2 = re.sub(r'(?m)^[ \t]*\d+[ \t]*=\s*\{[^}]*\}[ \t]*$\r?\n?', '', blk)
            for bm in re.finditer(r'(?m)^\s*([a-z_]+)\s*=\s*(\d+)\s*$', blk2):
                bsum[bm.group(1)] = bsum.get(bm.group(1), 0) + int(bm.group(2))
        for rm in re.finditer(r'(?m)^\s*([a-z_]+)\s*=\s*(\d+)\s*$',
                              (re.search(r'resources\s*=\s*\{([^}]*)\}', tt).group(1) if re.search(r'resources\s*=\s*\{([^}]*)\}', tt) else '')):
            res[rm.group(1)] = res.get(rm.group(1), 0) + int(rm.group(2))
    print(f'  {tag}: 合并 62 接受 5 州 → 省{len(provinces)} {provinces} man={man}')
    print(f'      建筑相加: {bsum}')
    print(f'      资源相加: {res}')
    # 重写 62 文件
    bld_lines = '\n'.join(f'\t\t\t{k} = {v}' for k, v in bsum.items())
    for pv, content in provblocks.items():
        bld_lines += f'\n\t\t\t{pv} = {{\n\t\t\t\t{content}\n\t\t\t}}'
    print(f'      省份块保留: {list(provblocks.keys())}')
    res_lines = '\n'.join(f'\t\t{k} = {v}' for k, v in res.items())
    # 提取原 62 的 history 块头（owner 等）
    hb = re.search(r'history\s*=\s*\{', t)
    depth, i = 0, hb.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    hist = t[hb.end():i]
    owner = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', hist)
    cores = re.findall(r'(?m)^\s*add_core_of\s*=\s*(\w+)', hist)
    newt = f'''state = {{
	id = 62
	name="DOT_STATE_62" # name="STATE_62"
	manpower = {man}
	state_category = town
	resources = {{
{res_lines}
	}}

	history = {{
		owner = {owner.group(1) if owner else "ABY"}
		{chr(10).join(f"add_core_of = {c}" for c in cores)}
		buildings = {{
{bld_lines}
		}}
	}}

	provinces = {{
		{' '.join(str(x) for x in provinces)}
	}}
}}
'''
    wr(p62, newt, raw, tag)
    # 删除 63/65/66/67 文件
    for sid in ('63', '65', '66', '67'):
        for f in glob.glob(os.path.join(base, 'history', 'states', f'{sid}-*.txt')):
            if APPLY:
                bd2 = os.path.join(BD, tag + '_states')
                os.makedirs(bd2, exist_ok=True)
                shutil.copy2(f, os.path.join(bd2, os.path.basename(f)))
                os.remove(f)
            print(f'  {tag}: 删除 {os.path.basename(f)}' + ('' if APPLY else '(DRY)'))
    # 引用迁移 63/65/66/67 → 62
    for rel, which in REF_EDITS:
        p = os.path.join(base, rel)
        if not os.path.exists(p):
            continue
        raw, t = rd(p)
        if which == '63':
            pats = [(r'((?:state|owns_state|controls_state|transfer_state|state_id)\s*=\s*)63(?!\d)', r'\g<1>62', None),
                    (r'(?m)^(\s*)63(\s*=\s*\{)', r'\g<1>62\g<2>', None)]
        elif which == '66/67':
            pats = [(r'((?:state|owns_state|controls_state|transfer_state|state_id)\s*=\s*)(?:66|67)(?!\d)', r'\g<1>62', None),
                    (r'(?m)^(\s*)(?:66|67)(\s*=\s*\{)', r'\g<1>62\g<2>', None)]
        else:  # 65/66 (INA)
            pats = [(r'((?:state|owns_state|controls_state|transfer_state|state_id)\s*=\s*)(?:65|66)(?!\d)', r'\g<1>62', None)]
        for pat, repl, e in pats:
            rx = re.compile(pat)
            n = len(rx.findall(t))
            if n:
                t = rx.sub(repl, t)
                print(f'  {tag} {os.path.basename(rel)}: 引用 {which}→62 ×{n} ✓' + ('' if APPLY else '(DRY)'))
        wr(p, t, raw, tag)

# ================= C) 补号 703-706 → 63/65/66/67 =================
print()
print('=== C) 补号：703/704/705/706 → 63/65/66/67 ===')
MAP = {'703': '63', '704': '65', '705': '66', '706': '67'}
for tag, base in COPIES:
    d = os.path.join(base, 'history', 'states')
    for old, new in MAP.items():
        fs = glob.glob(os.path.join(d, f'{old}-*.txt'))
        if not fs:
            print(f'  ★ {tag}: {old} 文件未找到')
            continue
        f = fs[0]
        raw, t = rd(f)
        t = re.sub(r'(?m)^(\s*id\s*=\s*)' + old + r'\b', r'\g<1>' + new, t, count=1)
        t = t.replace(f'name="DOT_STATE_{old}"', f'name="DOT_STATE_{new}"', 1)
        if APPLY:
            bd2 = os.path.join(BD, tag + '_states')
            os.makedirs(bd2, exist_ok=True)
            shutil.copy2(f, os.path.join(bd2, os.path.basename(f)))
            os.remove(f)
            open(os.path.join(d, f'{new}-State_{new}.txt'), 'wb').write(
                t.encode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'))
        print(f'  {tag}: {os.path.basename(f)} → {new}-State_{new}.txt ✓' + ('' if APPLY else '(DRY)'))
    # airports/rocketsites 键迁移：703-706 的值随州搬到 63/65/66/67；删原 63/65/66/67 键
    for fname in ('airports.txt', 'rocketsites.txt'):
        p = os.path.join(base, 'map', fname)
        raw, t = rd(p)
        vals = {}
        for l in t.split('\n'):
            m = re.match(r'^\s*(\d+)\s*=\s*\{([^}]*)\}', l)
            if m and m.group(1) in MAP:
                vals[m.group(1)] = m.group(2).strip()
        out = []
        for l in t.split('\n'):
            m = re.match(r'^(\s*)(\d+)(\s*=\s*\{)', l)
            if m:
                sid = m.group(2)
                if sid in ('63', '65', '66', '67'):
                    print(f'  {tag} {fname}: 删旧键 s{sid}' + ('' if APPLY else '(DRY)'))
                    continue
                if sid in MAP:
                    l = f'{MAP[sid]}={{{vals.get(sid, "")} }}'
                    print(f'  {tag} {fname}: s{sid}→s{MAP[sid]} (值 {vals.get(sid, "")})' + ('' if APPLY else '(DRY)'))
            out.append(l)
        wr(p, '\n'.join(out), raw, tag)

    # 703-706 引用扫描
    PAT703 = re.compile(r'((?:state|owns_state|controls_state|transfer_state|capital|state_id)\s*=\s*)(703|704|705|706)(?!\d)')
    BARE703 = re.compile(r'(?m)^(\s*)(703|704|705|706)(\s*=\s*\{)')
    for sub in ('common', 'events', 'history'):
        for dirpath, dirnames, filenames in os.walk(os.path.join(base, sub)):
            if 'states' in dirpath.split(os.sep):
                continue
            for fn in filenames:
                if not fn.endswith('.txt'):
                    continue
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, base)
                if 'resource_prospecting' in rel or '14_sea' in rel or '12_wuw' in rel:
                    continue
                raw2, t2 = rd(fp)
                hits = list(PAT703.finditer(t2)) + list(BARE703.finditer(t2))
                if hits:
                    for h in hits:
                        print(f'  ⚠ {tag} {rel}: {h.group(0)[:80]}')
                    t3 = PAT703.sub(lambda m: m.group(1) + MAP[m.group(2)], t2)
                    t3 = BARE703.sub(lambda m: m.group(1) + MAP[m.group(2)] + m.group(3), t3)
                    wr(fp, t3, raw2, tag)
    # buildings 行 col1 迁移
    p = os.path.join(base, 'map', 'buildings.txt')
    raw, t = rd(p)
    n = 0
    out = []
    for l in t.split('\n'):
        m = re.match(r'^(\d+)(;.*)$', l)
        if m and m.group(1) in MAP:
            l = MAP[m.group(1)] + m.group(2)
            n += 1
        out.append(l)
    wr(p, '\n'.join(out), raw, tag)
    print(f'  {tag}: buildings 行迁移 ×{n}' + ('' if APPLY else '(DRY)'))

# ================= D) 战略区 =================
print()
print('=== D) 战略区 id=46 马斯克海 ===')
REG_PROVS = ['4681', '3544', '4682', '4683', '4684', '860', '1531', '2282']
for tag, base in COPIES:
    p1 = os.path.join(base, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt')
    raw, t = rd(p1)
    ls = t.split('\n')
    keep = [l for l in ls if l.strip() and l.strip() not in REG_PROVS]
    dropped = len([l for l in ls if l.strip()]) - len(keep)
    wr(p1, '\r\n'.join(keep) + '\r\n', raw, tag + '_r1')
    print(f'  {tag}: 区域1 移除 {dropped} 省（预期 8）')
    p2 = os.path.join(base, 'map', 'strategicregions', 'DOT_Strategicregions_46.txt')
    content = 'strategic_region={\r\n\tid=46\r\n\tname="DOT_STRATEGICREGIONS_46"\r\n\tprovinces={\r\n'
    content += '\r\n'.join(REG_PROVS) + '\r\n\t}\r\n}\r\n'
    if APPLY:
        open(p2, 'wb').write(content.encode('utf-8'))
    print(f'  {tag}: 新建 DOT_Strategicregions_46.txt（{len(REG_PROVS)} 省）' + ('' if APPLY else '(DRY)'))

print()
print(f'模式: {"已应用" if APPLY else "DRY"}  备份: {BD}')

# -*- coding: utf-8 -*-
"""swap_tail_states.py v2 —— 708 ↔ 750 内容换位（用户指定，不含 718）
分道誓约之地（NAT）回到 708；原 708 海州换到 750。
联动：文件名/id 行/name 键/首都/buildings 第 1 列/本地化（名称随内容走）+ 脚本引用（严格模式）
仓库 + 副本；先备份；逐项回读验证。"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
MAP = {708: 750, 750: 708}   # 内容在 708 的搬到 750；在 750 的搬到 708

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'swap708_{stamp}')
os.makedirs(BD, exist_ok=True)


def load(p):
    raw = open(p, 'rb').read()
    return raw, raw.decode('utf-8-sig')


def save(p, t, bom):
    open(p, 'wb').write(((b'\xef\xbb\xbf' if bom else b'') + t.encode('utf-8')))


for tag, base in COPIES:
    ST = os.path.join(base, 'history', 'states')
    contents = {}
    for sid in (708, 750):
        p = os.path.join(ST, f'{sid}-State_{sid}.txt')
        raw, t = load(p)
        if tag == '仓库':
            shutil.copy2(p, os.path.join(BD, f'{sid}-State_{sid}.txt'))
        contents[sid] = (t, raw[:3] == b'\xef\xbb\xbf')
    for src, dst in MAP.items():
        t, bom = contents[src]
        t2 = re.sub(r'(\bid\s*=\s*)' + str(src) + r'\b', rf'\g<1>{dst}', t, count=1)
        t2 = t2.replace(f'name="DOT_STATE_{src}"', f'name="DOT_STATE_{dst}"')
        assert f'id = {dst}' in t2 and f'DOT_STATE_{dst}' in t2, f's{src}→{dst} 失败'
        save(os.path.join(ST, f'{dst}-State_{dst}.txt'), t2, bom)
    print(f'{tag}: 州文件 708↔750 换位完成')

    # 首都
    n_cap = 0
    for p in glob.glob(os.path.join(base, 'history', 'countries', '*.txt')):
        raw, t = load(p)
        t2, n = re.subn(r'(?m)^(\s*capital\s*=\s*)(\d+)',
                        lambda m: m.group(1) + str(MAP.get(int(m.group(2)), int(m.group(2)))), t)
        if n:
            save(p, t2, raw[:3] == b'\xef\xbb\xbf')
            n_cap += 1
    print(f'{tag}: 首都联动 {n_cap} 个文件')

    # buildings 第 1 列
    bp = os.path.join(base, 'map', 'buildings.txt')
    raw = open(bp, 'rb').read()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    lines = raw.decode('utf-8-sig').split(nl)
    n_b = 0
    for i, l in enumerate(lines):
        f7 = l.split(';')
        if len(f7) == 7 and f7[0].isdigit() and int(f7[0]) in MAP:
            f7[0] = str(MAP[int(f7[0])])
            lines[i] = ';'.join(f7)
            n_b += 1
    open(bp, 'wb').write(nl.join(lines).encode('utf-8'))
    print(f'{tag}: buildings 列联动 {n_b} 条')

    # 本地化（名称随内容走；用临时标记防止循环替换）
    n_loc = 0
    for p in glob.glob(os.path.join(base, 'localisation', 'simp_chinese', '*.yml')):
        raw, t = load(p)
        orig = t
        for src, dst in MAP.items():
            t = t.replace(f'DOT_STATE_{src}:', f'@@TMP_{dst}@@:')
        for src, dst in MAP.items():
            t = t.replace(f'@@TMP_{dst}@@:', f'DOT_STATE_{dst}:')
        if t != orig:
            save(p, t, raw[:3] == b'\xef\xbb\xbf')
            n_loc += 1
    print(f'{tag}: 本地化联动 {n_loc} 个文件')

    # 脚本引用（严格模式）
    TOKEN = re.compile(r'\b(owns_state|controls_state|has_full_control_of_state|transfer_state|state|capital)\s*=\s*(\d+)\b')
    n_s = 0
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ('.backups', '.backup', '.git', '备份')]
        for f in files:
            if not f.endswith('.txt'):
                continue
            p = os.path.join(root, f)
            rr = os.path.relpath(p, base).replace('\\', '/')
            if rr.startswith('history/states') or rr == 'map/buildings.txt':
                continue
            raw, t = load(p)
            t2 = TOKEN.sub(lambda m: m.group(1) + ' = ' + str(MAP.get(int(m.group(2)), int(m.group(2)))), t)
            if t2 != t:
                save(p, t2, raw[:3] == b'\xef\xbb\xbf')
                n_s += 1
    print(f'{tag}: 脚本引用联动 {n_s} 个文件')

# ---- 验证 ----
print()
kind = {}
for l in open(os.path.join(COPIES[0][1], 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        kind[int(a[0])] = a[4]
for tag, base in COPIES:
    ST = os.path.join(base, 'history', 'states')
    sea, land = [], []
    for sid in range(705, 751):
        f = os.path.join(ST, f'{sid}-State_{sid}.txt')
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        provs = [int(x) for x in (pm.group(1).split() if pm else [])]
        (sea if provs and all(kind.get(p) != 'land' for p in provs) else land).append(sid)
    print(f'{tag}: 海 {sea}')
    print(f'      陆(705+) {land}')
    t = open(os.path.join(ST, '708-State_708.txt'), encoding='utf-8-sig').read()
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    print(f'      s708 owner={om.group(1)}')
    loc = open(os.path.join(base, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml'),
               encoding='utf-8-sig', errors='replace').read()
    for k in (708, 750):
        mm = re.search(rf'DOT_STATE_{k}:0\s*"([^"]*)"', loc)
        print(f'      DOT_STATE_{k} = "{mm.group(1) if mm else "无"}"')

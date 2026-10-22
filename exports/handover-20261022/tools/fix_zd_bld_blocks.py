# -*- coding: utf-8 -*-
"""fix_zd_bld_blocks.py —— 重建 65 个至冬新州文件（buildings 块改用括号配对提取，
修复内嵌省级块被截断导致的括号失衡）；其余字段与 repair_zd_states 完全一致"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
BK = os.path.join(ROOT, '.backups', 'states_20261007_222357', 'history', 'states')


def extract_block(t, key):
    m = re.search(r'\b' + key + r'\s*=\s*\{', t)
    if not m:
        return None
    depth, i = 0, m.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                return t[m.start():i + 1]
        i += 1
    return None


def parse_state(t):
    d = {'provs': [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]}
    m = re.search(r'\bmanpower\s*=\s*([\d.]+)', t)
    d['manpower'] = float(m.group(1)) if m else 0.0
    m = re.search(r'state_category\s*=\s*(\w+)', t)
    d['cat'] = m.group(1) if m else 'wasteland'
    d['res'] = {}
    rm = re.search(r'resources\s*=\s*\{([^}]*)\}', t)
    if rm:
        for k, v in re.findall(r'(\w+)\s*=\s*([\d.]+)', rm.group(1)):
            d['res'][k] = d['res'].get(k, 0) + float(v)
    d['bld'] = extract_block(t, 'buildings')
    d['vp'] = []
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        xs = vm.group(1).split()
        for i in range(0, len(xs) - 1, 2):
            d['vp'].append((int(xs[i]), int(xs[i + 1])))
    d['cores'] = re.findall(r'add_core_of\s*=\s*(\w+)', t)
    return d


old_files = {}
for f in glob.glob(os.path.join(BK, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    if re.search(r'\bowner\s*=\s*SNE\b', t):
        old_files[sid] = parse_state(t)
old_provs = {q: s for s, d in old_files.items() for q in d['provs']}
div = json.load(open(os.path.join(ROOT, 'tools', 'zd_division.json'), encoding='utf-8'))
comp_provs = {int(c): sorted(v) for c, v in div['comp_provs'].items()}
overlap = {c: collections.Counter(old_provs[q] for q in provs if q in old_provs)
           for c, provs in comp_provs.items()}
new_id, taken = {}, set()
for c in sorted(comp_provs, key=lambda c: (-max(overlap[c].values()), c)):
    for o, _n in overlap[c].most_common():
        if o not in taken:
            new_id[c] = o
            taken.add(o)
            break

n_nested = 0
for c, provs in comp_provs.items():
    nid = new_id[c]
    hosts = collections.Counter(old_provs[q] for q in provs if q in old_provs)
    main_old = hosts.most_common(1)[0][0]
    d0 = old_files[main_old]
    if d0['bld'] and re.search(r'=\s*\{[^}]*\{', d0['bld']):
        n_nested += 1
    total_mp = sum(old_files[o]['manpower'] * hosts[o] / len(old_files[o]['provs']) for o in hosts)
    mp = max(0, int(round(total_mp / 1000.0)) * 1000)
    res = collections.defaultdict(float)
    for o in hosts:
        for k, v in old_files[o]['res'].items():
            res[k] += v * hosts[o] / len(old_files[o]['provs'])
    res_s = ''.join(f'\t\t{k} = {int(round(v))}\r\n' for k, v in sorted(res.items()) if round(v) > 0)
    vp_pairs = sorted({(pid, val) for o in hosts for pid, val in old_files[o]['vp']
                       if pid in set(provs)})
    vp_s = ''.join(f'\t\tvictory_points = {{ {pid} {val} }}\r\n' for pid, val in vp_pairs)
    bld_s = d0['bld'] + '\r\n' if d0['bld'] else ''
    cores = ['SNE'] + [x for x in d0['cores'] if x != 'SNE']
    core_s = ''.join(f'\t\tadd_core_of = {x}\r\n' for x in dict.fromkeys(cores))
    t = (f'state = {{\r\n'
         f'\tid = {nid}\r\n'
         f'\tname="DOT_STATE_{nid}"\r\n'
         f'\tmanpower = {mp}\r\n'
         f'\tstate_category = {d0["cat"]}\r\n'
         + (f'\tresources = {{\r\n{res_s}\t}}\r\n' if res_s else '')
         + f'\r\n\thistory = {{\r\n'
           f'\t\towner = SNE\r\n{core_s}{bld_s}{vp_s}'
           f'\t}}\r\n\r\n'
           f'\tprovinces = {{\r\n\t\t{" ".join(str(q) for q in provs)}\r\n\t}}\r\n'
           f'}}\r\n')
    open(os.path.join(ST, f'{nid}-State_{nid}.txt'), 'wb').write(t.encode('utf-8'))
print(f'重建 {len(comp_provs)} 个文件（内嵌 buildings 块 {n_nested} 个）')

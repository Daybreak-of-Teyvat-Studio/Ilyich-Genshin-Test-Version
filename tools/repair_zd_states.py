# -*- coding: utf-8 -*-
"""repair_zd_states.py —— 恢复被误删的 65 个至冬新州文件
数据源: .backups/states_20261007_222357（批次前备份）的 198 个旧 SNE 州
分组: tools/zd_division.json；id 继承逻辑与 apply_zd_redivision 完全一致（确定性重算）"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
BK = os.path.join(ROOT, '.backups', 'states_20261007_222357', 'history', 'states')


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
    bm = re.search(r'(buildings\s*=\s*\{[^}]*)\}', t, re.S)
    d['bld'] = (bm.group(1) + '}') if bm else None
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
        old_files[sid] = (f, parse_state(t))
assert len(old_files) == 198, f'备份里 SNE 州 {len(old_files)} ≠ 198'
old_ids = sorted(old_files)
old_provs = {q: s for s, (_f, d) in old_files.items() for q in d['provs']}

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
old2new = {}
for o in old_ids:
    cands = [c for c in comp_provs if o in overlap[c]]
    best = max(cands, key=lambda c: (overlap[c][o], 1 if new_id[c] == o else 0, -c))
    old2new[o] = new_id[best]

# 前置检查：目标 id 不得已存在文件（防覆盖）
cur_ids = {int(re.match(r'(\d+)-', os.path.basename(f)).group(1))
           for f in glob.glob(os.path.join(ST, '*.txt')) if re.match(r'\d+-', os.path.basename(f))}
clash = sorted(set(new_id.values()) & cur_ids)
assert not clash, f'目标 id 已有文件: {clash}'

n_vp = 0
for c, provs in comp_provs.items():
    nid = new_id[c]
    hosts = collections.Counter(old_provs[q] for q in provs if q in old_provs)
    main_old = hosts.most_common(1)[0][0]
    d0 = old_files[main_old][1]
    total_mp = sum(old_files[o][1]['manpower'] * hosts[o] / len(old_files[o][1]['provs'])
                   for o in hosts)
    mp = max(0, int(round(total_mp / 1000.0)) * 1000)
    res = collections.defaultdict(float)
    for o in hosts:
        d1 = old_files[o][1]
        for k, v in d1['res'].items():
            res[k] += v * hosts[o] / len(d1['provs'])
    res_s = ''.join(f'\t\t{k} = {int(round(v))}\r\n' for k, v in sorted(res.items()) if round(v) > 0)
    vp_pairs = sorted({(pid, val) for o in hosts for pid, val in old_files[o][1]['vp']
                       if pid in set(provs)})
    n_vp += len(vp_pairs)
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
    with open(os.path.join(ST, f'{nid}-State_{nid}.txt'), 'wb') as f:
        f.write(t.encode('utf-8'))
print(f'恢复 65 个新州文件（VP {n_vp} 条）')

# 终验
fs = glob.glob(os.path.join(ST, '*.txt'))
ids = sorted(int(re.match(r'(\d+)-', os.path.basename(f)).group(1))
             for f in fs if re.match(r'\d+-', os.path.basename(f)))
sne = []
for f in fs:
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    if 'owner = SNE' in t:
        sne.append(int(re.search(r'\bid\s*=\s*(\d+)', t).group(1)))
print(f'终验: 文件 {len(fs)}，范围 {ids[0]}-{ids[-1]}，SNE 州 {len(sne)} 个')
print(f'新州 id: {sorted(sne)}')
empty = [f for f in fs if not re.search(r'provinces\s*=\s*\{[^}*]', open(f, encoding='utf-8-sig', errors='replace').read() + '}')]
print(f'空省州: {empty or "无"}')

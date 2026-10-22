# -*- coding: utf-8 -*-
"""scan_ownerless.py —— 扫描无 owner 的州文件：区分海州（正常）与陆州（致命）"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

# definition: 省是否为陆地
kind = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        kind[int(a[0])] = a[4]

no_owner, no_core, no_bld = [], [], []
all_states = {}
for f in sorted(glob.glob(os.path.join(ST, '*.txt'))):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in (pm.group(1).split() if pm else [])]
    land_n = sum(1 for p in provs if kind.get(p) == 'land')
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    cores = re.findall(r'add_core_of\s*=\s*(\w+)', t)
    bld = re.search(r'buildings\s*=\s*\{', t) is not None
    cat = re.search(r'state_category\s*=\s*(\w+)', t)
    all_states[sid] = dict(provs=len(provs), land=land_n, owner=om.group(1) if om else None,
                           cores=cores, bld=bld, cat=cat.group(1) if cat else None)
    if not om:
        no_owner.append(sid)
    if not cores:
        no_core.append(sid)
    if not bld:
        no_bld.append(sid)

print(f'州总数 {len(all_states)}')
print(f'无 owner: {len(no_owner)}')
print(f'无 add_core_of: {len(no_core)}')
print(f'无 buildings 块: {len(no_bld)}')

landless = [s for s in no_owner if all_states[s]['land'] == 0]
withland = [s for s in no_owner if all_states[s]['land'] > 0]
print()
print(f'无 owner 且无陆地省（=海州，正常）: {len(landless)} 个')
print(f'无 owner 但含陆地省（=问题州！）: {len(withland)} 个')
print()
print('问题州明细:')
for s in withland:
    d = all_states[s]
    print(f'  s{s}: 省{d["provs"]}个(陆{d["land"]}) cat={d["cat"]} cores={d["cores"]} bld={d["bld"]}')

print()
print('无 core 但无 owner 以外的（有 owner 无 core）:')
nocore_owned = [s for s in no_core if s not in no_owner]
print(f'  {len(nocore_owned)} 个: {nocore_owned[:40]}')

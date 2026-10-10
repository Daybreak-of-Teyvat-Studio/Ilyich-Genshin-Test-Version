# -*- coding: utf-8 -*-
"""final_sweep.py —— 穷尽检查
1) 全树 hash 比对 仓库 vs 副本（堵 mtime 盲区）
2) 所有 OOB 部队 location 指向海州/不存在省
3) 所有国家首都 vs 实际拥有
"""
import os, re, sys, glob, hashlib, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
SKIP = {'.backups', '.backup', '__pycache__'}

# ---- 1) 全树 hash ----
def tree_hash(base):
    out = {}
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, base)
            h = hashlib.md5()
            with open(p, 'rb') as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b''):
                    h.update(chunk)
            out[rel] = h.hexdigest()
    return out

print('正在全树哈希（17k 文件）...')
tr, td = tree_hash(REPO), tree_hash(DEP)
only_r = set(tr) - set(td)
only_d = set(td) - set(tr)
diff = [k for k in set(tr) & set(td) if tr[k] != td[k]]
print(f'仓库 {len(tr)} / 副本 {len(td)}；只在仓库 {len(only_r)}；只在副本 {len(only_d)}；内容不同 {len(diff)}')
for k in list(only_r)[:8]:
    print('  R only:', k)
for k in list(only_d)[:8]:
    print('  D only:', k)
for k in diff[:10]:
    print('  differ:', k)

# ---- 2) OOB location 扫描 ----
G = REPO
kind = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 4 and a[0].strip().isdigit() and int(a[0]) > 0:
        kind[int(a[0])] = a[4]
all_provs = set(kind)
sea_states, all_states = set(), set()
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    all_states.add(sid)
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in (pm.group(1).split() if pm else [])]
    if provs and all(kind.get(p) != 'land' for p in provs):
        sea_states.add(sid)

print()
print('=== OOB 部队 location 异常（不存在省 / 海省）===')
loc_bad = []
for f in glob.glob(os.path.join(G, 'history', 'units', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'(?m)^\s*location\s*=\s*(\d+)', t):
        q = int(m.group(1))
        if q not in all_provs:
            loc_bad.append((os.path.basename(f), q, '不存在'))
        elif kind.get(q) != 'land':
            loc_bad.append((os.path.basename(f), q, kind.get(q)))
print(f'  异常 {len(loc_bad)}: {loc_bad[:20]}')

# ---- 3) 首都拥有检查 ----
print()
print('=== 首都未拥有的国家（非致命性参考）===')
st_owner = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    st_owner[sid] = om.group(1) if om else None
bad = []
for p in sorted(glob.glob(os.path.join(G, 'history', 'countries', '*.txt'))):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    tag = os.path.basename(p).split(' ')[0].split('-')[0].strip()
    for m in re.finditer(r'(?m)^\s*capital\s*=\s*(\d+)', t):
        c = int(m.group(1))
        o = st_owner.get(c)
        if o != tag:
            bad.append((tag, c, o))
for b in bad:
    print(' ', b)
print(f'  共 {len(bad)} 个')

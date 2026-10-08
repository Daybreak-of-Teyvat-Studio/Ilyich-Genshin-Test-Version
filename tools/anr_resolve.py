# -*- coding: utf-8 -*-
"""anr_resolve.py —— 解析 ANR 控制地标新闻文件：地标名 → gamma VP → 新省号/州号
同时检查 DVA_focustree 的 60={ 块语境"""
import os, re, sys, glob, json

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# gamma VP 名 → 省
g_vp = {}
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_vp.setdefault(m.group(2), []).append(int(m.group(1)))
# gamma 省→州
g_p2s, g_owner = {}, {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    g_owner[sid] = om.group(1) if om else '海'
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        g_p2s[int(x)] = sid


def resolve(name):
    """地标名 → (gamma 省候选, 途径)"""
    if name in g_vp:
        return g_vp[name], '精确'
    cands = [k for k in g_vp if name and (name in k or k in name)]
    if cands:
        return sorted({p for k in cands for p in g_vp[k]}), f'近似({cands[:3]})'
    return [], ''


P = os.path.join(G, 'common', 'on_actions', 'ANR_influence_on_actions.txt')
t = open(P, encoding='utf-8-sig', errors='replace').read().splitlines()
print('=== ANR 地标解析 ===')
cur_name = None
rows = []
for i, l in enumerate(t, 1):
    s = l.strip()
    if s.startswith('#') and s[1:].strip() and not s.startswith('##') and not re.match(r'#\d+ ', s):
        if not any(k in s for k in ('ROOT is', 'FROM is', 'FROM.FROM', '蒙德势力', '攻陷新闻')):
            cur_name = s.lstrip('#').strip()
    m = re.search(r'\bstate\s*=\s*(\d+)', s)
    if m and cur_name:
        rows.append((cur_name, 'state', int(m.group(1)), i))
    m = re.search(r'controls_province\s*=\s*(\d+)', s)
    if m and cur_name:
        rows.append((cur_name, 'province', int(m.group(1)), i))
for name, kind, val, line in rows:
    cands, how = resolve(name)
    new_prov = cands[0] if cands else None
    new_state = g_p2s.get(new_prov) if new_prov else None
    print(f'  [{line}] {name} {kind}={val} → ' +
          (f'gamma p{new_prov}（州 s{new_state} owner {g_owner.get(new_state)}） via {how}'
           + (f'（多候选 {cands[:5]}）' if len(cands) > 1 else '') if cands else '✗ 无法解析'))

print()
print('=== DVA_focustree 60={ 块语境 ===')
P2 = os.path.join(G, 'common', 'national_focus', 'DVA_focustree.txt')
t2 = open(P2, encoding='utf-8-sig', errors='replace').read().splitlines()
for ln in (262, 277, 407, 1825, 1844, 1919):
    print(f'--- 行 {ln} 前 2 / 后 4 ---')
    for j in range(max(0, ln - 3), min(len(t2), ln + 4)):
        print(f'  {j+1}: {t2[j].rstrip()[:100]}')

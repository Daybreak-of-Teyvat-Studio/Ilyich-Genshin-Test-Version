# -*- coding: utf-8 -*-
"""build_beta_gamma_bridge.py —— 构建 beta→gamma id 桥（以本地化为桥）
州桥:   beta州英文名 → beta中文loc → gamma同名州（fallback: gamma同名VP→省→其州）
省桥:   beta VICTORY_POINTS_省号 中文名 → gamma同名VP → gamma省号
输出: tools/beta_gamma_bridge.json（只读操作）"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
GAMMA = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# ---------- beta ----------
beta_states = {}
for f in glob.glob(os.path.join(BETA, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    nm = re.search(r'name\s*=\s*"([^"]+)"', t)
    provs = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    vp = [(int(a), int(b)) for a, b in re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', t)]
    beta_states[sid] = {'en': nm.group(1) if nm else None,
                        'provs': [int(x) for x in (provs.group(1).split() if provs else [])],
                        'vp': vp}
beta_loc = {}
for p in glob.glob(os.path.join(BETA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*([A-Za-z][\w ]*?):\d*\s*"([^"]*)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        beta_loc.setdefault(m.group(1).strip(), m.group(2))
beta_vp_cn = {}
for p in glob.glob(os.path.join(BETA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        beta_vp_cn[int(m.group(1))] = m.group(2)

# ---------- gamma ----------
g_state_cn = collections.defaultdict(list)   # 中文名 -> [gid]
g_state_key = {}                             # gid -> 中文名
for p in glob.glob(os.path.join(GAMMA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s*"([^"]*)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        gid, cn = int(m.group(1)), m.group(2)
        g_state_key[gid] = cn
        if cn != '*':
            g_state_cn[cn].append(gid)
g_vp_cn = collections.defaultdict(list)      # 中文名 -> [pid]
g_vp_key = {}                                # pid -> 中文名
for p in glob.glob(os.path.join(GAMMA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        pid, cn = int(m.group(1)), m.group(2)
        g_vp_key[pid] = cn
        if cn != '*':
            g_vp_cn[cn].append(pid)
# gamma 省 → 州
g_p2s = {}
for f in glob.glob(os.path.join(GAMMA, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        g_p2s[int(x)] = sid

# ---------- 州桥 ----------
state_bridge = {}
n_ok = n_ambig = n_nogamma = n_nocn = 0
for bid in sorted(beta_states):
    en = beta_states[bid]['en']
    cn = beta_loc.get(en) if en else None
    rec = {'beta_id': bid, 'en': en, 'cn': cn, 'gamma_id': None, 'status': '', 'note': ''}
    if not cn:
        rec['status'] = '✗ beta无中文名'
        n_nocn += 1
    elif cn in g_state_cn:
        gids = g_state_cn[cn]
        if len(gids) == 1:
            rec['gamma_id'] = gids[0]
            rec['status'] = '✓'
            n_ok += 1
        else:
            rec['gamma_id'] = gids[0]
            rec['status'] = '⚠ gamma重名'
            rec['note'] = f"候选 {gids}"
            n_ambig += 1
    else:
        # fallback: gamma 同名 VP → 省 → 其州
        if cn in g_vp_cn:
            pids = g_vp_cn[cn]
            gids = sorted({g_p2s[p] for p in pids if p in g_p2s})
            if len(gids) == 1:
                rec['gamma_id'] = gids[0]
                rec['status'] = '✓ VP桥'
                rec['note'] = f"经VP省{pids}"
                n_ok += 1
            elif gids:
                rec['gamma_id'] = gids[0]
                rec['status'] = '⚠ VP桥多州'
                rec['note'] = f"VP省{pids}→州{gids}"
                n_ambig += 1
            else:
                rec['status'] = '✗ VP省无州'
                n_nogamma += 1
        else:
            rec['status'] = '✗ gamma无同名'
            n_nogamma += 1
    state_bridge[bid] = rec

# ---------- 省桥 ----------
prov_bridge = {}
n_pok = n_pambig = n_pno = 0
for pid, cn in sorted(beta_vp_cn.items()):
    rec = {'beta_pid': pid, 'cn': cn, 'gamma_pid': None, 'status': ''}
    if cn in g_vp_cn:
        pids = g_vp_cn[cn]
        if len(pids) == 1:
            rec['gamma_pid'] = pids[0]
            rec['status'] = '✓'
            n_pok += 1
        else:
            rec['gamma_pid'] = pids[0]
            rec['status'] = '⚠ gamma重名VP'
            rec['note'] = f"候选 {pids}"
            n_pambig += 1
    else:
        rec['status'] = '✗ gamma无同名VP'
        n_pno += 1
    prov_bridge[pid] = rec

out = {
    'state_bridge': state_bridge, 'prov_bridge': prov_bridge,
    'g_state_key': {str(k): v for k, v in g_state_key.items()},
    'g_vp_key': {str(k): v for k, v in g_vp_key.items()},
    'g_p2s': {str(k): v for k, v in g_p2s.items()},
    'stat': {'state': {'✓': n_ok, '⚠': n_ambig, '✗gamma无': n_nogamma, '✗beta无名': n_nocn},
             'prov': {'✓': n_pok, '⚠': n_pambig, '✗': n_pno},
             'beta_vp_total': len(beta_vp_cn), 'gamma_vp_named': len(g_vp_key)}}
with open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"州桥: ✓{n_ok} ⚠重名{n_ambig} ✗gamma无{len([r for r in state_bridge.values() if r['status'].startswith('✗') and 'beta' not in r['status']])} ✗beta无名{n_nocn}")
print(f"省桥: ✓{n_pok} ⚠重名{n_pambig} ✗{n_pno}")
print('已存 tools/beta_gamma_bridge.json')

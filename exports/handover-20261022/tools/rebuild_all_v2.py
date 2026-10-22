# -*- coding: utf-8 -*-
"""rebuild_all_v2.py —— 迁移数据链 v2（三合一）
1) 桥 v2：只认【活键】（州文件实际使用）为可信 gamma 目标；同号死键=陈旧；含人工映射
2) 扫描 v2：扩展模式（province=/province_id/controls_province/provinces={}/set_province_name id/add_victory_points）
3) Excel v2：桌面 beta至gamma_id迁移对照表.xlsx（全部分类与明细）
"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# ============ 1. 桥 v2 ============
# beta 地标
b_vp = {}
for p in glob.glob(os.path.join(B, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        b_vp[int(m.group(1))] = m.group(2)
b_by_name = collections.defaultdict(list)
for pid, nm in b_vp.items():
    b_by_name[nm].append(pid)

# gamma loc 键 + 活键集
g_vp = {}
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_vp[int(m.group(1))] = m.group(2)
used = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for m in re.finditer(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', t):
        used[int(m.group(1))] = (sid, int(m.group(2)))
live = set(used)

# gamma 省→州/owner + 州名
g_p2s, g_owner, g_sname = {}, {}, {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    g_owner[sid] = om.group(1) if om else ('海' if not re.search(r'wasteland', t) else '荒地')
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        g_p2s[int(x)] = sid
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_sname[int(m.group(1))] = m.group(2)

# 人工映射
manual = {'state': {}, 'province': {}}
mp = os.path.join(ROOT, 'tools', 'beta_gamma_manual_map.json')
if os.path.exists(mp):
    manual.update(json.load(open(mp, encoding='utf-8')))

prov_bridge = {}
for name, bpids in b_by_name.items():
    for bnum in bpids:
        gpids = [x for x in g_vp if g_vp[x] == name]
        live_p = [x for x in gpids if x in live]
        dead_same = [x for x in gpids if x not in live and x == bnum]
        rec = {'beta_pid': bnum, 'cn': name, 'gamma_pid': None, 'status': '', 'note': ''}
        if bnum in {int(k) for k in manual.get('province', {}) if manual['province'][k] != 'skip'}:
            rec['gamma_pid'] = int(manual['province'][str(bnum)])
            rec['status'] = '✓ 人工映射'
        elif live_p:
            rec['gamma_pid'] = live_p[0]
            if live_p[0] == bnum:
                rec['status'] = '✓ 同号活键'
            else:
                rec['status'] = '✓ 修正（活键）'
            rec['note'] = f'州 s{g_p2s.get(live_p[0])}（{g_owner.get(g_p2s.get(live_p[0]))}）'
        elif gpids:
            rec['status'] = '⚠ 仅死键（陈旧移植）'
            rec['note'] = f'死键 {gpids}'
        else:
            rec['status'] = '✗ gamma无名'
        prov_bridge[bnum] = rec

# 州桥 v2：beta 州名 → gamma 州名；同号=可疑
bloc = {}
for p in glob.glob(os.path.join(B, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*([A-Za-z][\w ]*?):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        bloc.setdefault(m.group(1).strip(), m.group(2))
g_state_by_name = collections.defaultdict(list)
for sid, nm in g_sname.items():
    if nm and nm != '*':
        g_state_by_name[nm].append(sid)

state_bridge = {}
for f in glob.glob(os.path.join(B, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    nm_en = re.search(r'name\s*=\s*"([^"]+)"', t)
    if not nm_en:
        continue
    cn = bloc.get(nm_en.group(1))
    rec = {'beta_id': sid, 'en': nm_en.group(1), 'cn': cn, 'gamma_id': None, 'status': '', 'note': ''}
    if cn and cn in g_state_by_name:
        gids = g_state_by_name[cn]
        rec['gamma_id'] = gids[0]
        rec['status'] = '⚠ 同号（需核对）' if gids[0] == sid else '✓'
        if len(gids) > 1:
            rec['note'] = f'多候选 {gids}'
    else:
        rec['status'] = '✗ gamma无同名州'
    state_bridge[sid] = rec

json.dump({'state_bridge': state_bridge,
           'prov_bridge': {str(k): v for k, v in prov_bridge.items()},
           'live': sorted(live), 'dead': sorted(set(g_vp) - live),
           'used': {str(k): v for k, v in used.items()},
           'g_p2s': {str(k): v for k, v in g_p2s.items()},
           'g_owner': {str(k): v for k, v in g_owner.items()},
           'g_sname': {str(k): v for k, v in g_sname.items()}},
          open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

stat = collections.Counter(v['status'].split('（')[0] for v in prov_bridge.values())
print('桥 v2 省侧状态:')
for k, v in stat.most_common():
    print(f'  {k}: {v}')
sstat = collections.Counter(v['status'].split('（')[0] for v in state_bridge.values())
print('桥 v2 州侧状态:')
for k, v in sstat.most_common():
    print(f'  {k}: {v}')
print(f'活键 {len(live)}，死键 {len(set(g_vp) - live)}')

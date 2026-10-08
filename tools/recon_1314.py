# -*- coding: utf-8 -*-
"""recon_1314.py —— 核实"高塔孤王的遗址"案例全链
A) beta: VP 1314 的名字 / 它所在州（风龙领？）
B) gamma: 孤王高塔 VP 在哪个省 Z / 其州与 owner；p1314 现在的州与 owner
C) gamma 脚本里现存的 1314 引用（迁移后残留）
D) 桥数据里 1314 的状态
"""
import os, re, sys, glob, json

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
GAMMA = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# ---------- A. beta ----------
beta_vp = {}
for p in glob.glob(os.path.join(BETA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        beta_vp[int(m.group(1))] = m.group(2)
print('A. beta:')
print('  VICTORY_POINTS_1314 =', repr(beta_vp.get(1314)))
print('  含"高塔"/"孤王"的 beta VP:',
      [(k, v) for k, v in beta_vp.items() if '高塔' in v or '孤王' in v])
# beta p1314 所在州
for f in glob.glob(os.path.join(BETA, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if pm and re.search(r'\b1314\b', pm.group(1)):
        sid = re.search(r'\bid\s*=\s*(\d+)', t).group(1)
        nm = re.search(r'name\s*=\s*"([^"]+)"', t)
        print(f'  beta p1314 在州 s{sid}，name={nm.group(1) if nm else "?"}')
        break

# ---------- B. gamma ----------
g_vp = {}
for p in glob.glob(os.path.join(GAMMA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_vp[int(m.group(1))] = m.group(2)
hits = [(k, v) for k, v in g_vp.items() if '高塔' in v or '孤王' in v]
print('B. gamma:')
print('  含"高塔"/"孤王"的 gamma VP:', hits)

g_p2s, g_s2o, g_sname = {}, {}, {}
for f in glob.glob(os.path.join(GAMMA, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    g_s2o[sid] = om.group(1) if om else '海'
    nm = re.search(r'name\s*=\s*"DOT_STATE_(\d+)"', t)
    g_sname[sid] = int(nm.group(1)) if nm else sid
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        g_p2s[int(x)] = sid
for k, v in hits:
    st = g_p2s.get(k)
    print(f'  gamma VP {k}「{v}」在省，所属州 s{st}（owner {g_s2o.get(st)}）')
st1314 = g_p2s.get(1314)
print(f'  gamma p1314 在州 s{st1314}（owner {g_s2o.get(st1314)}）')
# 风龙领 州
for f in glob.glob(os.path.join(GAMMA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s*"([^"]*)"',
                         open(f, encoding='utf-8-sig', errors='replace').read(), re.M):
        if '风龙' in m.group(2) or '龙领' in m.group(2):
            print(f'  gamma 州名「{m.group(2)}」= s{m.group(1)}')
# beta 风龙领 州号 + 其 VP
bloc = {}
for p in glob.glob(os.path.join(BETA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*([A-Za-z][\w ]*?):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        bloc.setdefault(m.group(1).strip(), m.group(2))
for f in glob.glob(os.path.join(BETA, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    nm = re.search(r'name\s*=\s*"([^"]+)"', t)
    cn = bloc.get(nm.group(1)) if nm else None
    if cn and ('风龙' in cn or '龙领' in cn):
        sid = re.search(r'\bid\s*=\s*(\d+)', t).group(1)
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        vps = re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', t)
        print(f'  beta 州 s{sid}「{cn}」省 {pm.group(1).split() if pm else []}')
        print(f'    VP: ' + '; '.join(f'p{p}「{beta_vp.get(int(p))}」{v}' for p, v in vps))

# ---------- C. gamma 脚本残留 1314 ----------
print('C. gamma 脚本中的 1314 引用:')
n = 0
for root, dirs, files in os.walk(GAMMA):
    dirs[:] = [d for d in dirs if d not in ('.backups', '.git', '备份')]
    for f in files:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(root, f)
        rr = os.path.relpath(p, GAMMA).replace('\\', '/')
        if rr.startswith('history/states') or rr == 'map/buildings.txt':
            continue
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        for l in t.splitlines():
            if re.search(r'\b1314\b', l):
                n += 1
                if n <= 30:
                    print(f'  [{rr}] {l.strip()[:110]}')
print(f'  共 {n} 行')

# ---------- D. 桥 ----------
br = json.load(open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), encoding='utf-8'))
print('D. 桥:')
print('  state_bridge[1314]:', br['state_bridge'].get('1314'))
print('  prov_bridge[1314]:', br['prov_bridge'].get('1314'))

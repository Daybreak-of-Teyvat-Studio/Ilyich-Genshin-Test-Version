# -*- coding: utf-8 -*-
"""recon_beta_bridge.py —— 侦察 beta/gamma 本地化桥数据
输出: beta 州英文名及其中文 loc 命中率、beta VP 覆盖、gamma 侧名字覆盖"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
GAMMA = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# beta 州文件
beta_states = {}
for f in glob.glob(os.path.join(BETA, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    nm = re.search(r'name\s*=\s*"([^"]+)"', t)
    provs = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    vp = [(int(a), int(b)) for a, b in re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', t)]
    beta_states[sid] = {'name': nm.group(1) if nm else None,
                        'provs': provs.group(1).split() if provs else [],
                        'vp': vp}
print(f'beta 州 {len(beta_states)} 个；有 name 的 {sum(1 for d in beta_states.values() if d["name"])}')

# beta loc：英文 key → 中文（simp_chinese 全部 yml）
beta_loc = {}
for p in glob.glob(os.path.join(BETA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*([A-Za-z][\w ]*?):\d*\s*"([^"]*)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        beta_loc.setdefault(m.group(1).strip(), m.group(2))
print(f'beta 中文 loc key {len(beta_loc)} 条')
named = [d['name'] for d in beta_states.values() if d['name']]
hit = [n for n in named if n in beta_loc]
print(f'beta 州英文名在中文 loc 命中: {len(hit)}/{len(named)}')
for n in named[:10]:
    print(f'  {n!r} -> {beta_loc.get(n, "(无)!")!r}')

# beta VP
beta_vp = {}
for p in glob.glob(os.path.join(BETA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        beta_vp[int(m.group(1))] = m.group(2)
print(f'beta VP 本地化: {len(beta_vp)} 省')
vp_in_states = sum(1 for d in beta_states.values() for pid, _ in d['vp'] if pid in beta_vp)
vp_total = sum(len(d['vp']) for d in beta_states.values())
print(f'beta 州内 VP {vp_total} 个，其中名字在 loc 的 {vp_in_states}')

# gamma 侧
g_state_name, g_vp = {}, {}
for p in glob.glob(os.path.join(GAMMA, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s*"([^"]*)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_state_name[int(m.group(1))] = m.group(2)
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"', open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_vp[int(m.group(1))] = m.group(2)
print(f'gamma 州名 {len(g_state_name)} 条（非* {sum(1 for v in g_state_name.values() if v != "*")}），VP {len(g_vp)} 条')
dup = [k for k, v in collections.Counter(g_state_name.values()).items() if v > 1 and k != '*']
print(f'gamma 重名州: {dup[:10]}')
dupv = [k for k, v in collections.Counter(g_vp.values()).items() if v > 1]
print(f'gamma 重名 VP: {dupv[:10]}')

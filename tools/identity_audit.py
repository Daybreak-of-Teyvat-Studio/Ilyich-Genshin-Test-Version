# -*- coding: utf-8 -*-
"""identity_audit.py —— 抽查"名称桥同号对"的陈旧率：
beta VP pX 名称 N → gamma 同号 pX；检查 gamma pX 所属州的 owner 和名字与 N 的地理是否矛盾。"""
import os, re, sys, json, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

br = json.load(open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), encoding='utf-8'))
identity = [(int(k), v['cn']) for k, v in br['prov_bridge'].items()
            if v.get('gamma_pid') and int(k) == v['gamma_pid'] and str(v.get('status', '')).startswith('✓')]
print(f'同号对总数: {len(identity)}')

# gamma 省→州→owner
g_p2s, g_owner, g_sname = {}, {}, {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    g_owner[sid] = om.group(1) if om else '海'
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        g_p2s[int(x)] = sid
gname = {}
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        gname[int(m.group(1))] = m.group(2)

# 地区关键词 → 期望 tag 集合（粗略）
REGION = {
    '蒙德': {'MOT', 'DVA', 'LAW', 'RAG', 'FAV', 'GUN', 'HZH'},   # 蒙德及旧贵族系等
    '璃月': {'LYY', 'NAT', 'PBF', 'NDK'},
    '稻妻': {'INA', 'SAN'},
    '须弥': {'SUM', 'SDH', 'SGD', 'BRF', 'SGS'},
    '枫丹': {'FON', 'FOD', 'DVA', 'FOM', 'NSC', 'NCP'},
    '纳塔': {'NMN', 'NCE', 'NFF', 'NPS'},
    '至冬': {'SNE'},
}
print()
sus = 0
for pid, nm in sorted(identity):
    if not nm:
        continue
    st = g_p2s.get(pid)
    own = g_owner.get(st)
    exp = None
    for kw, tags in REGION.items():
        if kw in nm:
            exp = tags
            break
    flag = ''
    if exp and own and own not in exp and own != '海':
        flag = f'⚠ 名/地不符（名含{kw}，实际 owner={own}）'
        sus += 1
    if pid <= 140 or pid in (1314, 442):
        print(f'  p{pid}「{nm}」→ gamma 州 s{st}（{g_sname.get(st)}，owner {own}） {flag}')
print(f'\n关键词可判定的矛盾数: {sus}（样本打印前若干）')
print(f'同号对示例（前 30）：' + ', '.join(f'{p}:{n}' for p, n in sorted(identity)[:30]))

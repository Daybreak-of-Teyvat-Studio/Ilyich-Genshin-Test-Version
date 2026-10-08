# -*- coding: utf-8 -*-
"""landmark_audit.py —— 地标名审计：beta 表 vs gamma 表
规则：gamma 中同名字不同号的条目 = 修正版（可信映射）；
      只有同号条目 = 疑似陈旧（flag）；无名或需人工。
输出：tools/landmark_audit.json + 控制台摘要"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# beta 表
b_vp = {}
for p in glob.glob(os.path.join(B, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        b_vp[int(m.group(1))] = m.group(2)
b_by_name = collections.defaultdict(list)
for pid, nm in b_vp.items():
    b_by_name[nm].append(pid)

# gamma 表
g_vp = {}
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_vp[int(m.group(1))] = m.group(2)
g_by_name = collections.defaultdict(list)
for pid, nm in g_vp.items():
    g_by_name[nm].append(pid)

# gamma 省→州/owner
g_p2s, g_owner = {}, {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    g_owner[sid] = om.group(1) if om else '海'
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        g_p2s[int(x)] = sid

rows = []
stat = collections.Counter()
for name, bpids in sorted(b_by_name.items()):
    if not name or name in ('?',):
        continue
    gpids = g_by_name.get(name, [])
    bnum = bpids[0]
    corrected = [x for x in gpids if x != bnum]
    same = [x for x in gpids if x == bnum]
    if not gpids:
        st = 'gamma无此名'
    elif corrected:
        st = '✓ 有修正条目'
    elif same:
        st = '⚠ 仅同号（疑似陈旧）'
    else:
        st = '?'
    stat[st] += 1
    rows.append({'name': name, 'beta': bnum, 'gamma_corrected': corrected, 'gamma_same': same, 'status': st})

print('=== 统计（beta 全部地标名）===')
for k, v in stat.most_common():
    print(f'  {k}: {v}')

print()
print('=== ANR 文件涉及的地标逐个看 ===')
ANR = ['西风大教堂', '蒙德城门', '风起地', '千风神殿', '劳伦斯堡', '达达乌帕城', '清泉镇',
       '安德琉斯谷', '风王高塔', '营地城', '芬德尼尔之顶', '晨曦酒庄', '璃月港', '玉京台',
       '黄金屋', '层岩巨渊', '庆云顶', '孤云阁']
for nm in ANR:
    r = [x for x in rows if x['name'] == nm]
    if r:
        x = r[0]
        corr = x['gamma_corrected']
        msg = ''
        if corr:
            p = corr[0]
            msg = f'→ gamma p{p}（州 s{g_p2s.get(p)} owner {g_owner.get(g_p2s.get(p))}）'
        print(f'  {nm}: beta={x["beta"]} gamma_corrected={corr} same={x["gamma_same"]} {x["status"]} {msg}')
    else:
        print(f'  {nm}: beta 表里没有此名')

json.dump(rows, open(os.path.join(ROOT, 'tools', 'landmark_audit.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print()
print('已存 tools/landmark_audit.json')

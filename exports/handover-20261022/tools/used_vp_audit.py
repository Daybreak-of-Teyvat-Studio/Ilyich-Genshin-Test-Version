# -*- coding: utf-8 -*-
"""used_vp_audit.py —— 判定 gamma VP 键的生死：
'被州文件引用（活）' vs '孤儿（死，疑似陈旧移植）'
并核对 214 个同号可疑键的生死分布。"""
import os, re, sys, glob, collections, json

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# 州文件里实际使用的 (省, 值)
used = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for m in re.finditer(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', t):
        used[int(m.group(1))] = (sid, int(m.group(2)))
print(f'州文件中使用的 VP 条目: {len(used)} 个')

# gamma loc keys
g_vp = {}
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_vp[int(m.group(1))] = m.group(2)
print(f'gamma VP loc 键: {len(g_vp)} 个')

live = [k for k in g_vp if k in used]
dead = [k for k in g_vp if k not in used]
print(f'活键（loc 有 + 州文件引用）: {len(live)}')
print(f'死键（loc 有 + 州文件无引用）: {len(dead)}')

# 州文件引用但无 loc 的
no_loc = [k for k in used if k not in g_vp]
print(f'州文件引用但缺 loc 的键: {len(no_loc)}  {sorted(no_loc)[:20]}')

# 214 同号可疑键的生死
la = json.load(open(os.path.join(ROOT, 'tools', 'landmark_audit.json'), encoding='utf-8'))
sus = [x for x in la if x['status'].startswith('⚠')]
sus_dead = [x for x in sus if x['beta'] not in used]
sus_live = [x for x in sus if x['beta'] in used]
print()
print(f'214 同号可疑中：死键 {len(sus_dead)}，活键 {len(sus_live)}')
print('活键样例（同号但被州文件使用！）:')
for x in sus_live[:20]:
    st, val = used[x['beta']]
    print(f'  p{x["beta"]}「{x["name"]}」在 s{st} 值{val}')
# 修正键的生死
corr = [x for x in la if x['status'].startswith('✓')]
corr_live = [x for x in corr if x['gamma_corrected'] and x['gamma_corrected'][0] in used]
corr_dead = [x for x in corr if x['gamma_corrected'] and x['gamma_corrected'][0] not in used]
print()
print(f'51 修正条目中：活键 {len(corr_live)}，死键 {len(corr_dead)}')
for x in corr_dead[:10]:
    print(f'  {x["name"]}: beta={x["beta"]} corrected={x["gamma_corrected"]}（死键）')

# 孤儿 loc 键是否集中在 beta 编号段
json.dump({'live': sorted(live), 'dead': sorted(dead), 'no_loc': sorted(no_loc)},
          open(os.path.join(ROOT, 'tools', 'vp_live_dead.json'), 'w'), indent=1)
print()
print('已存 tools/vp_live_dead.json')

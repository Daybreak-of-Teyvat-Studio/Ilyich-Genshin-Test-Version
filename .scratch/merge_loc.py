# -*- coding: utf-8 -*-
"""合并全部 VP 本地化来源 + STATE 州名 → 构建 Beta VP 名字典"""
import sys, os, re, collections
sys.stdout.reconfigure(encoding='utf-8')
LOC = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version\localisation\simp_chinese'

# ① VP 本地化（从全部 yml 收集）
vp_loc = {}
for f in sorted(os.listdir(LOC)):
    if not f.endswith('.yml'):
        continue
    p = os.path.join(LOC, f)
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8', errors='replace')
    for m in re.finditer(r'^\s*(VICTORY_POINTS_\d+):\d*\s+"([^"]*)"', t, re.M):
        vp_loc[m.group(1)] = m.group(2)

print(f'VP 本地化 key 总数: {len(vp_loc)}')
# 样例
for k in list(vp_loc)[:5]:
    print(f'  {k} = {vp_loc[k]}')

# ② STATE_ 州名
state_loc = {}
for f in sorted(os.listdir(LOC)):
    if not f.endswith('.yml'):
        continue
    p = os.path.join(LOC, f)
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8', errors='replace')
    for m in re.finditer(r'^\s*(STATE_\d+):\d*\s+"([^"]*)"', t, re.M):
        state_loc[m.group(1)] = m.group(2)
print(f'STATE_ 州名 key 总数: {len(state_loc)}')

# ③ 保存合并结果（供 beta_vp_map3.py 使用）
import json
out_path = os.path.join(os.path.dirname(LOC), '..', 'beta_loc_cache.json')
data = {'vp_loc': vp_loc, 'state_loc': state_loc}
with open(out_path, 'w', encoding='utf-8') as fh:
    json.dump(data, fh, ensure_ascii=False, indent=1)
print(f'已保存 {out_path}')

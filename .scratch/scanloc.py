# -*- coding: utf-8 -*-
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
LOC = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version\localisation\simp_chinese'
total_vp = total_state = 0
vp_by_file = {}
state_by_file = {}
for f in sorted(os.listdir(LOC)):
    if not f.endswith('.yml'):
        continue
    p = os.path.join(LOC, f)
    raw = open(p, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    t = raw.decode('utf-8-sig' if bom else 'utf-8', errors='replace')
    nv = len(re.findall(r'VICTORY_POINTS_\d+:', t))
    ns = len(re.findall(r'STATE_\d+:', t))
    if nv:
        vp_by_file[f] = nv
    if ns:
        state_by_file[f] = ns
    total_vp += nv
    total_state += ns

print(f'VP 本地化条目总数: {total_vp}')
for f, n in sorted(vp_by_file.items(), key=lambda x: -x[1])[:8]:
    print(f'  {f}: {n}')
print(f'STATE_ 本地化条目总数: {total_state}')
for f, n in sorted(state_by_file.items(), key=lambda x: -x[1])[:8]:
    print(f'  {f}: {n}')

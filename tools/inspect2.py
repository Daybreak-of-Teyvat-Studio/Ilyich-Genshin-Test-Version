# -*- coding: utf-8 -*-
"""inspect2.py —— 只读：loc 键实况 + 三个不对称文件的差异内容"""
import os, re, sys, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

print('=== gamma 州名文件中的 708/750/分道誓约 ===')
for tag, base in (('仓库', REPO), ('副本', DEP)):
    p = os.path.join(base, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'--- {tag} ---')
    for l in t.splitlines():
        if re.match(r'^\s*DOT_STATE_(708|750|709)\s*:', l) or '分道誓约' in l:
            print('  ', repr(l.strip()[:100]))
    print('   mtime:', datetime.datetime.fromtimestamp(os.path.getmtime(p)))

print()
print('=== DOT_state_names_l 里的 708/750（老文件）===')
for tag, base in (('仓库', REPO), ('副本', DEP)):
    p = os.path.join(base, 'localisation', 'simp_chinese', 'DOT_state_names_l_simp_chinese.yml')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    hits = [l.strip()[:90] for l in t.splitlines() if re.match(r'^\s*(DOT_STATE|VICTORY_POINTS)_(708|750)\s*:', l)]
    print(f'  {tag}: {hits}')

print()
print('=== 三个不对称文件的差异摘要 ===')
for rel in ('common/national_focus/DVA_focustree.txt',
            'common/on_actions/ANR_influence_on_actions.txt',
            'localisation/simp_chinese/DOT_state_names_l_simp_chinese.yml'):
    rp = os.path.join(REPO, *rel.split('/'))
    dp = os.path.join(DEP, *rel.split('/'))
    rt = open(rp, encoding='utf-8-sig', errors='replace').read()
    dt = open(dp, encoding='utf-8-sig', errors='replace').read()
    print(f'--- {rel} ---')
    print(f'  仓库 mtime {datetime.datetime.fromtimestamp(os.path.getmtime(rp))}，副本 mtime {datetime.datetime.fromtimestamp(os.path.getmtime(dp))}')
    for label, t in (('仓库', rt), ('副本', dt)):
        marks = []
        if '433 = {' in t:
            marks.append(f'433块×{t.count(chr(52)+chr(51)+chr(51)+chr(32)+chr(61)+chr(32)+chr(123))}')
        if re.search(r'(?m)^\s*60 = \{', t):
            marks.append('60块仍在')
        if 'province = 442' in t:
            marks.append('province=442')
        if 'province = 1314' in t:
            marks.append('province=1314')
        if 'controls_province = 442' in t:
            marks.append('controls_province=442')
        if 'controls_province = 1314' in t:
            marks.append('controls_province=1314')
        if 'VICTORY_POINTS_1314' in t:
            marks.append('含VP1314键')
        print(f'    {label}: {marks}')

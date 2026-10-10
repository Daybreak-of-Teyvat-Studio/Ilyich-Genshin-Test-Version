# -*- coding: utf-8 -*-
"""diff_4files.py —— 4 个嫌疑文件 vs 编辑前备份的精确 diff（含行尾检查）"""
import os, sys, difflib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BK = os.path.join(ROOT, '.backups', 'tower1314_20261008_130216')
if not os.path.isdir(BK):
    # 找实际时间戳目录
    import glob
    cands = glob.glob(os.path.join(ROOT, '.backups', 'tower1314_*'))
    BK = sorted(cands)[-1] if cands else ''
print('备份目录:', BK)

pairs = [
    ('common/national_focus/DVA_focustree.txt', os.path.join(BK, 'DVA_focustree.txt')),
    ('common/on_actions/ANR_influence_on_actions.txt', os.path.join(BK, 'ANR_influence_on_actions.txt')),
    ('localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml',
     os.path.join(BK, 'DOT_state_names_gamma_l_simp_chinese.yml')),
    ('localisation/simp_chinese/DOT_state_names_l_simp_chinese.yml',
     os.path.join(ROOT, '.backups', 'states_20261007_222357', 'DOT_state_names_l_simp_chinese.yml')),
]
for rel, oldp in pairs:
    newp = os.path.join(D, *rel.split('/'))
    if not os.path.exists(oldp):
        print(f'!! 缺备份: {oldp}')
        continue
    a = open(oldp, 'rb').read()
    b = open(newp, 'rb').read()
    la = a.decode('utf-8-sig').splitlines(keepends=True)
    lb = b.decode('utf-8-sig').splitlines(keepends=True)
    diff = [x for x in difflib.unified_diff([x.rstrip(chr(13) + chr(10)) for x in la],
                                            [x.rstrip(chr(13) + chr(10)) for x in lb],
                                            lineterm='', n=0)]
    nl_old = a.count(b'\r\n'), a.count(b'\n')
    nl_new = b.count(b'\r\n'), b.count(b'\n')
    print(f'\n=== {rel} ===')
    print(f'  旧: {len(a)}B CRLF={nl_old[0]} LF总={nl_old[1]}；新: {len(b)}B CRLF={nl_new[0]} LF总={nl_new[1]}')
    print(f'  diff 行数: {len(diff)}')
    for x in diff[:24]:
        print('   ', x[:150])

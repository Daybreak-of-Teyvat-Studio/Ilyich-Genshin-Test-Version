# -*- coding: utf-8 -*-
"""revert_tower4.py —— 把 4 个嫌疑文件精确回滚到编辑前（仓库+副本）
focustree / ANR / state_names_gamma ← tower1314 备份
state_names_l ← states_20261007_222357 备份（预处理掉 1314 键删除）"""
import os, shutil, sys, hashlib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK1 = os.path.join(ROOT, '.backups', 'tower1314_20261008_130216')
BK2 = os.path.join(ROOT, '.backups', 'states_20261007_222357')

JOBS = [
    ('common/national_focus/DVA_focustree.txt', os.path.join(BK1, 'DVA_focustree.txt')),
    ('common/on_actions/ANR_influence_on_actions.txt', os.path.join(BK1, 'ANR_influence_on_actions.txt')),
    ('localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml',
     os.path.join(BK1, 'DOT_state_names_gamma_l_simp_chinese.yml')),
    ('localisation/simp_chinese/DOT_state_names_l_simp_chinese.yml',
     os.path.join(BK2, 'DOT_state_names_l_simp_chinese.yml')),
]

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()

for rel, src in JOBS:
    assert os.path.exists(src), f'缺备份 {src}'
    for base, tag in ((REPO, '仓库'), (DEP, '副本')):
        dst = os.path.join(base, *rel.split('/'))
        shutil.copy2(src, dst)
    print(f'{rel} 已回滚（源: {os.path.basename(os.path.dirname(src))}）')

print()
print('=== 验证：仓库与备份逐字节一致 ===')
for rel, src in JOBS:
    dst = os.path.join(REPO, *rel.split('/'))
    same = md5(src) == md5(dst)
    print(f'  {rel}: {"✓ 一致" if same else "✗ 不一致"}')

print()
print('=== 验证：两边一致 ===')
bad = 0
for rel, src in JOBS:
    a = os.path.join(REPO, *rel.split('/'))
    b = os.path.join(DEP, *rel.split('/'))
    if md5(a) != md5(b):
        bad += 1
        print(f'  ✗ 不一致: {rel}')
print('全部一致 ✓' if not bad else f'{bad} 个不一致')

# 复核 ANR 关键两行回到 60/1314
t = open(os.path.join(REPO, 'common', 'on_actions', 'ANR_influence_on_actions.txt'), encoding='utf-8-sig').read()
import re
m = re.search(r'#风王高塔[\s\S]{0,200}?state = (\d+)[\s\S]{0,120}?controls_province = (\d+)', t)
print('ANR 塔块现状: state =', m.group(1), '/ controls_province =', m.group(2))

# -*- coding: utf-8 -*-
"""fix_tower_1314.py v2 —— 高塔孤王案例修复（CRLF 安全）
1) DVA_focustree.txt: province=1314 → 442 ×2；id=1314 → 442；60/76 = { → 433
2) ANR: 风王高塔块 controls_province 1314 → 442；state 60 → 433
3) 删陈旧 loc 键 VICTORY_POINTS_1314
4) 写人工映射 province 1314 → 442
仓库 + 副本都改；逐项回读验证"""
import os, re, sys, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'tower1314_{stamp}')
os.makedirs(BD, exist_ok=True)

# CRLF 安全的行首锚定替换：(?m)^([ \t]*)KEY[ \t]*=[ \t]*\{[ \t]*\r?$
PAT60 = re.compile(r'(?m)^([ \t]*)60[ \t]*=[ \t]*\{[ \t]*\r?$')
PAT76 = re.compile(r'(?m)^([ \t]*)76[ \t]*=[ \t]*\{[ \t]*\r?$')
PATID = re.compile(r'(?m)^([ \t]*)id[ \t]*=[ \t]*1314[ \t]*\r?$')

for base, tag in ((REPO, '仓库'), (DEP, '副本')):
    # 1) focustree
    p = os.path.join(base, 'common', 'national_focus', 'DVA_focustree.txt')
    if base == REPO:
        shutil.copy2(p, BD)
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    t, n1 = re.subn(r'province = 1314', 'province = 442', t)
    assert n1 == 2, f'{tag} focustree province 1314 数 {n1}'
    t, n2 = PATID.subn(lambda m: m.group(1) + 'id = 442', t)
    assert n2 == 1, f'{tag} focustree id 1314 数 {n2}'
    t, n3 = PAT60.subn(lambda m: m.group(1) + '433 = {', t)
    assert n3 == 5, f'{tag} focustree 60 块数 {n3}'
    t, n4 = PAT76.subn(lambda m: m.group(1) + '433 = {', t)
    assert n4 == 2, f'{tag} focustree 76 块数 {n4}'
    open(p, 'wb').write(((b'\xef\xbb\xbf' if raw[:3] == b'\xef\xbb\xbf' else b'') + t.encode('utf-8')))
    print(f'{tag} focustree: 60×{n3} 76×{n4} → 433，province×{n1} id×{n2} → 442')

    # 2) ANR（只动风王高塔块）
    p = os.path.join(base, 'common', 'on_actions', 'ANR_influence_on_actions.txt')
    if base == REPO:
        shutil.copy2(p, BD)
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    t, m1 = re.subn(r'(#风王高塔[\s\S]{0,300}?FROM\.FROM = \{ )state = 60( \})',
                    lambda m: m.group(1) + 'state = 433' + m.group(2), t)
    assert m1 == 1, f'{tag} ANR state 数 {m1}'
    t, m2 = re.subn(r'(#风王高塔[\s\S]{0,300}?controls_province = )1314\b',
                    lambda m: m.group(1) + '442', t)
    assert m2 == 1, f'{tag} ANR prov 数 {m2}'
    open(p, 'wb').write(((b'\xef\xbb\xbf' if raw[:3] == b'\xef\xbb\xbf' else b'') + t.encode('utf-8')))
    print(f'{tag} ANR: state→433 ×{m1}，province→442 ×{m2}')

    # 3) loc 键
    p = os.path.join(base, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
    if base == REPO:
        shutil.copy2(p, BD)
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    t, n5 = re.subn(r'(?m)^[ \t]*VICTORY_POINTS_1314:\d*[ \t]*"[^"]*"[ \t]*\r?\n?', '', t)
    open(p, 'wb').write(((b'\xef\xbb\xbf' if raw[:3] == b'\xef\xbb\xbf' else b'') + t.encode('utf-8')))
    print(f'{tag} loc: 删 VICTORY_POINTS_1314 ×{n5}')

# 4) 人工映射
mp = os.path.join(ROOT, 'tools', 'beta_gamma_manual_map.json')
open(mp, 'w', encoding='utf-8').write(
    '{\n "province": {"1314": 442},\n "_注释": "1314(高塔孤王的遗址/风王高塔) -> 442(孤王的高塔)：2026-10-08 用户确认修复"\n}\n')
print('人工映射已写:', mp)

# 回读验证
print()
for base, tag in ((REPO, '仓库'), (DEP, '副本')):
    t1 = open(os.path.join(base, 'common', 'national_focus', 'DVA_focustree.txt'), encoding='utf-8-sig').read()
    t2 = open(os.path.join(base, 'common', 'on_actions', 'ANR_influence_on_actions.txt'), encoding='utf-8-sig').read()
    t3 = open(os.path.join(base, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml'), encoding='utf-8-sig').read()
    print(f'{tag}: focustree 1314残留={t1.count("1314")} 442出现={t1.count("= 442")} 433块={len(re.findall(chr(94) + r"([ \t]*)433[ \t]*=[ \t]*\{", t1, re.M))}')
    print(f'      ANR 1314残留={t2.count("1314")} state433={t2.count("state = 433")} prov442={t2.count("= 442")}')
    print(f'      loc 1314键{"还在!" if "VICTORY_POINTS_1314" in t3 else "已删"}')

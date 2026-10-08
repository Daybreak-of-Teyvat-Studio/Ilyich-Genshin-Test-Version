# -*- coding: utf-8 -*-
"""anr_origin.py —— 查 ANR 文件里数字的来源
A) beta 版同名文件里这些块是什么数字（前身对照）
B) 我们 10-07 迁移的备份里 ANR 文件是否被改过、改了什么
C) 关键省在 beta/gamma 的表与位置"""
import os, re, sys, glob, difflib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# A) beta 版文件
bp = os.path.join(B, 'common', 'on_actions', 'ANR_influence_on_actions.txt')
print('A) beta 版 ANR 文件存在:', os.path.exists(bp))
if os.path.exists(bp):
    t = open(bp, encoding='utf-8-sig', errors='replace').read().splitlines()
    for i, l in enumerate(t, 1):
        if 'controls_province' in l or re.search(r'\bstate\s*=\s*\d+', l) or (l.strip().startswith('#') and '大教堂' in l):
            print(f'  {i}: {l.strip()[:110]}')

# B) 我们迁移的备份
BD = os.path.join(ROOT, '.backups', 'beta_ids_20261007_233117')
print()
print('B) 10-07 迁移备份里含 ANR 的文件:', [f for f in os.listdir(BD) if 'ANR' in f] if os.path.isdir(BD) else '无备份目录')
cur = os.path.join(G, 'common', 'on_actions', 'ANR_influence_on_actions.txt')
bck = [os.path.join(BD, f) for f in os.listdir(BD) if 'ANR_influence' in f] if os.path.isdir(BD) else []
if bck:
    a = open(bck[0], encoding='utf-8-sig', errors='replace').read().splitlines()
    b = open(cur, encoding='utf-8-sig', errors='replace').read().splitlines()
    diff = list(difflib.unified_diff(a, b, lineterm='', n=1))
    print(f'  备份→当前 差异行数: {len([x for x in diff if x.startswith(("+", "-")) and not x.startswith(("+++", "---"))])}')
    for x in diff[:40]:
        print('   ', x[:130])
else:
    print('  备份里没有该文件（说明 10-07 迁移没动它）')

# C) 关键省位置
b_vp = {}
for p in glob.glob(os.path.join(B, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        b_vp.setdefault(m.group(2), []).append(int(m.group(1)))
g_vp = {}
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        g_vp.setdefault(m.group(2), []).append(int(m.group(1)))
print()
print('C) 名字在两表的号：')
for nm in ('清泉镇', '达达乌帕城', '晨曦酒庄', '西风大教堂'):
    print(f'  {nm}: beta={b_vp.get(nm)} gamma={g_vp.get(nm)}')

# 位置
def loc(base, pid):
    for f in glob.glob(os.path.join(base, 'history', 'states', '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        if pm and re.search(r'\b' + str(pid) + r'\b', pm.group(1)):
            sid = re.search(r'\bid\s*=\s*(\d+)', t).group(1)
            om = re.search(r'\bowner\s*=\s*(\w+)', t)
            return f's{sid}({om.group(1) if om else "海"})'
    return '?'

print()
print('C2) 关键省位置（gamma）：')
for pid in (4529, 4567, 4741, 5799, 4548, 1189, 4371, 4436, 4540, 4340):
    print(f'  gamma p{pid}: {loc(G, pid)}')
print('C3) 关键省位置（beta）：')
for pid in (4529, 4567, 4741, 4548):
    print(f'  beta p{pid}: {loc(B, pid)}')

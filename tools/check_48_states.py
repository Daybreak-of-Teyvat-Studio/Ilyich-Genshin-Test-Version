# -*- coding: utf-8 -*-
"""check_48_states.py —— 检查日志报缺失的 48 个州（6,7,8,9,56-99）两个副本的健康度"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\history\states'
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version\history\states'
IDS = [6, 7, 8, 9] + list(range(56, 100))
print(f'检查 {len(IDS)} 个州号')
bad = 0
for sid in IDS:
    fs = os.path.join(R, f'{sid}-State_{sid}.txt')
    fd = os.path.join(D, f'{sid}-State_{sid}.txt')
    er = os.path.getsize(fs) if os.path.exists(fs) else -1
    ed = os.path.getsize(fd) if os.path.exists(fd) else -1
    ok = er > 100 and ed > 100
    if not ok:
        bad += 1
        print(f'  s{sid}: 仓库 {er}B 副本 {ed}B ✗')
    elif sid <= 9 or sid == 56 or sid == 99:
        t = open(fs, encoding='utf-8-sig', errors='replace').read()
        om = re.search(r'\bowner\s*=\s*(\w+)', t)
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        print(f'  s{sid}: {er}B owner={om.group(1) if om else "海"} 省数={len(pm.group(1).split()) if pm else 0}')
print(f'不健康数: {bad}')
# 全部 750 个州文件健康快查（副本）
n0 = 0
import glob
for f in glob.glob(os.path.join(D, '*.txt')):
    if os.path.getsize(f) == 0:
        n0 += 1
        print('  零字节:', os.path.basename(f))
print(f'副本零字节州文件: {n0}')

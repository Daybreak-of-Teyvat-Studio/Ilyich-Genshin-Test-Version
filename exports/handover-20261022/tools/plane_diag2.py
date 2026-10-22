# -*- coding: utf-8 -*-
"""plane_diag2.py —— bomb_locks 原版定义 + mod 装备文件 + 现日志检查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'

print('=== 原版 bomb_locks 定义 ===')
p = os.path.join(V, 'common', 'units', 'equipment', 'modules', '00_plane_modules.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
i = t.find('bomb_locks = {')
print(t[i:i + 400])

print()
print('=== 原版 small_plane_airframe_0（archetype）是否被 mod 覆盖 ===')
print('mod 有无 00_plane_modules.txt:', os.path.exists(os.path.join(G, 'common', 'units', 'equipment', 'modules', '00_plane_modules.txt')))
print('mod 有无 00_plane_airframes.txt:', os.path.exists(os.path.join(G, 'common', 'units', 'equipment', '00_plane_airframes.txt')))

print()
print('=== mod units/equipment 目录 ===')
for p in sorted(glob.glob(os.path.join(G, 'common', 'units', 'equipment', '**', '*.txt'), recursive=True)):
    print('  ', os.path.relpath(p, G))

print()
print('=== 当前日志中的 闲云机/create_equipment_variant ===')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()
n = 0
for l in ls:
    if '闲云机' in l or 'create_equipment_variant' in l or 'Unbuildable' in l or 'equipment' in l.lower() and 'MF' in l:
        n += 1
        if n <= 15:
            print(' ', l[:190])
print(f'  共 {n} 行')

print()
print('=== 10-08 日志里的完整错误文本（找持久副本）===')
# 从备份或既有输出里找
for cand in ['C:\\Users\\LR\\.zcode\\cli\\exec\\sess_3c421fb8-e84d-47d4-a44c-53452b380660']:
    for f in glob.glob(os.path.join(cand, 'call_*-stdout.log')):
        c = open(f, encoding='utf-8', errors='replace').read()
        if 'Unbuildable plane' in c:
            for l in c.splitlines():
                if 'Unbuildable plane' in l:
                    print(' ', f.split('\\')[-1][:40], ':', l.strip()[:240])
                    break

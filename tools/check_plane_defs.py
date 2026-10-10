# -*- coding: utf-8 -*-
"""check_plane_defs.py —— mod 装备文件是否重定义飞机底盘/模块"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

FILES = ['common/units/equipment/Baron_Bunny.txt', 'common/units/equipment/DOT_food.txt',
         'common/units/equipment/Ilyich_Tech_Equipment.txt', 'common/units/equipment/Wind_Glinder.txt',
         'common/units/equipment/fast_boat.txt',
         'common/units/equipment/modules/DVA_plane_modules.txt']
for rel in FILES:
    p = os.path.join(G, *rel.split('/'))
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    hits = []
    for kw in ('small_plane_airframe', 'bomb_locks', 'fixed_main_weapon_slot', 'archetype',
               'cas_weapon', 'plane', 'airframe'):
        if kw in t:
            hits.append(kw)
    print(f'{rel}: {os.path.getsize(p)}B；命中关键词 {hits}')
    # 打印 archetype/equipment 块头
    for m in re.finditer(r'(?m)^(\w+)\s*=\s*\{', t):
        pass
print()
print('=== DVA_plane_modules.txt 全文件（可能覆盖原版模块）===')
p = os.path.join(G, 'common', 'units', 'equipment', 'modules', 'DVA_plane_modules.txt')
print(open(p, encoding='utf-8-sig', errors='replace').read()[:3000])

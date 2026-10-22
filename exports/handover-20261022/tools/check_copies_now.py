# -*- coding: utf-8 -*-
"""check_copies_now.py —— 检查修复是否还在两个副本里 + 文件被动过的痕迹"""
import os, sys, time, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

def mt(p):
    return time.strftime('%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p)))

for tag, base in (('仓库', G), ('副本', D)):
    print('=' * 70)
    print(f'【{tag}】{base}')
    # 1 airports
    p = os.path.join(base, 'map', 'airports.txt')
    if os.path.exists(p):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        nl = len([x for x in t.split('\n') if x.strip()])
        print(f'  airports.txt: {os.path.getsize(p)}B {nl}行 mtime={mt(p)} 首行={t.splitlines()[0][:40] if t.splitlines() else "空"}')
    else:
        print('  airports.txt: 不存在')
    # 2 rocketsites
    p = os.path.join(base, 'map', 'rocketsites.txt')
    if os.path.exists(p):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        nl = len([x for x in t.split('\n') if x.strip()])
        print(f'  rocketsites.txt: {os.path.getsize(p)}B {nl}行 mtime={mt(p)} 首行={t.splitlines()[0][:40] if t.splitlines() else "空"}')
    # 3 supply_nodes
    p = os.path.join(base, 'map', 'supply_nodes.txt')
    if os.path.exists(p):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        nl = len([x for x in t.split('\n') if x.strip()])
        print(f'  supply_nodes.txt: {os.path.getsize(p)}B {nl}行 mtime={mt(p)}')
    # 4 buildings 317 fix
    p = os.path.join(base, 'map', 'buildings.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    fix1 = '317;special_project_facility_spawn;1798.00;11.91;1394.00;2.45;0' in t
    bad1 = '317;special_project_facility_spawn;1796.00;11.91;1396.00;2.45;0' in t
    print(f'  buildings.txt: mtime={mt(p)} 317修复行={fix1} 旧坏行仍在={bad1}')
    # 5 INA 变体
    p = os.path.join(base, 'history', 'countries', 'INA - Inazuma.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'  INA - Inazuma.txt: mtime={mt(p)} Sumeru_Class出现={t.count("Sumeru_Class")} 变体块数={t.count("create_equipment_variant")}')
    # 6 FAV 变体
    p = os.path.join(base, 'history', 'countries', 'FAV - Favonius.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'  FAV - Favonius.txt: mtime={mt(p)} Mondstadt_Class={t.count("Mondstadt_Class")} 变体块数={t.count("create_equipment_variant")}')
    # 7 地标 entity
    p = os.path.join(base, 'gfx', 'entities', 'DOT_buildings.asset')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'  DOT_buildings.asset: mtime={mt(p)} institute实体={"building_landmark_institute_of_tower" in t} 总数={t.count("entity = {")}')
    # 8 VAN 空壳
    p = os.path.join(base, 'history', 'units', 'VAN_1936_naval.txt')
    print(f'  VAN_1936_naval.txt: {"存在" if os.path.exists(p) else "★不存在"} {os.path.getsize(p) if os.path.exists(p) else ""}B mtime={mt(p) if os.path.exists(p) else "-"}')
    # 9 PRI 去重
    import re
    p = os.path.join(base, 'history', 'units', 'PRI_1936_Naval.txt')
    if os.path.exists(p):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        names = re.findall(r'ship = \{ name = "([^"]+)"', t)
        print(f'  PRI_1936_Naval.txt: {len(names)}舰 唯一={len(set(names))} mtime={mt(p)}')
    print()

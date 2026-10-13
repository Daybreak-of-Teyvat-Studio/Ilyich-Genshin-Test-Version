# -*- coding: utf-8 -*-
"""fix_landmark_entities.py —— 给两个缺 entity 的地标补 entity 块（照 DOT_buildings.asset 既有风格）"""
import os, re, sys, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'landmark_ent_{stamp}')
os.makedirs(BD, exist_ok=True)

ADD = '''

entity = {
    name = "building_landmark_institute_of_tower"
    pdxmesh = "landmark_big_ben_mesh"
    default_state = "idle"
    state = { name = "idle"\t\t\t\tanimation = "idle"       \t\tanimation_blend_time = 0.3 animation_speed = 1.0 looping = no }
    scale = 0.30
}

entity = {
    name = "building_landmark_Lei_Line_research_center"
    pdxmesh = "landmark_kremlin_mesh"
    default_state = "idle"
    state = { name = "idle"\t\t\t\tanimation = "idle"       \t\tanimation_blend_time = 0.3 animation_speed = 1.0 looping = no }
    scale = 0.30
}
'''

for tag, base in COPIES:
    p = os.path.join(base, 'gfx', 'entities', 'DOT_buildings.asset')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    if 'building_landmark_institute_of_tower' in t:
        print(f'  {tag}: 已存在，跳过')
        continue
    t2 = t.rstrip('\r\n') + '\n' + ADD
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_DOT_buildings.asset'))
        open(p, 'wb').write(t2.encode('utf-8'))
    # 括号平衡检查
    bal = t2.count('{') - t2.count('}')
    print(f'  {tag}: 追加 2 个 entity 块 ✓  大括号平衡={bal}  文件 {len(t2)} 字符')

# 验证
print()
for tag, base in COPIES:
    p = os.path.join(base, 'gfx', 'entities', 'DOT_buildings.asset')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    ok1 = 'name = "building_landmark_institute_of_tower"' in t
    ok2 = 'name = "building_landmark_Lei_Line_research_center"' in t
    n = len(re.findall(r'^entity = \{', t, re.M))
    print(f'  {tag}: institute={ok1} lei_line={ok2} entity块数={n}')
print(f'模式: {"已应用" if APPLY else "DRY"}  备份: {BD}')

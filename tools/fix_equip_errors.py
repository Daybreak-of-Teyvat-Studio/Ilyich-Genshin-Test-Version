# -*- coding: utf-8 -*-
"""fix_equip_errors.py —— 三处装备/部队错误修复（仓库+副本，先备份）
1) DOT_on_actions.txt: 闲云机-26型 战斗机底盘+对地武器 → 改为 CAS 底盘（照抄原版结构）
2) MOT - Mondstadt.txt: 风车菊级/蒲公英级 删除不存在的 front_1_custom_slot 行
3) DVA_1936.txt: location = 2463（璃月的省）→ 442（DVA 首都州省份）
"""
import os, re, sys, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]

# 闲云机-26型 新块（照原版 Hs 123 结构：CAS 底盘 0 + bomb_locks + engine_1_1x + special_1=empty）
OLD26 = '''create_equipment_variant = {
					name = "闲云机-26型"
					type = small_plane_airframe_0
					modules = {
						fixed_main_weapon_slot = bomb_locks
						fixed_auxiliary_weapon_slot_1 = empty
						engine_type_slot = engine_1_1x
						special_type_slot_1 = empty
						special_type_slot_2 = empty
					}
					icon = GFX_antiair5_medium
				}'''
NEW26 = '''create_equipment_variant = {
					name = "闲云机-26型"
					type = small_plane_cas_airframe_0
					modules = {
						fixed_main_weapon_slot = bomb_locks
						engine_type_slot = engine_1_1x
						special_type_slot_1 = empty
					}
					icon = GFX_antiair5_medium
				}'''

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'equipfix_{stamp}')
os.makedirs(BD, exist_ok=True)


def load(p):
    raw = open(p, 'rb').read()
    return raw, raw.decode('utf-8-sig')


def save(p, t, bom):
    open(p, 'wb').write(((b'\xef\xbb\xbf' if bom else b'') + t.encode('utf-8')))


for tag, base in COPIES:
    # 1) 闲云机-26型
    p = os.path.join(base, 'common', 'on_actions', 'DOT_on_actions.txt')
    if tag == '仓库':
        shutil.copy2(p, os.path.join(BD, 'DOT_on_actions.txt'))
    raw, t = load(p)
    t = t.replace('\r\n', '\n')
    # 用宽松匹配：找到 闲云机-26型 变体块并整体替换
    m = re.search(r'create_equipment_variant = \{\n\s*name = "闲云机-26型"[\s\S]*?\n\s*\}', t)
    assert m, f'{tag}: 闲云机-26型 未找到'
    t2 = t[:m.start()] + NEW26.replace('\r\n', '\n') + t[m.end():]
    assert 'small_plane_cas_airframe_0' in t2
    open(p, 'wb').write(t2.encode('utf-8'))
    print(f'{tag}: 闲云机-26型 → CAS 底盘 ✓')

    # 2) MOT 船变体
    p = os.path.join(base, 'history', 'countries', 'MOT - Mondstadt.txt')
    if tag == '仓库':
        shutil.copy2(p, os.path.join(BD, 'MOT - Mondstadt.txt'))
    raw, t = load(p)
    t2, n = re.subn(r'(?m)^[ \t]*front_1_custom_slot[ \t]*=[ \t]*ship_(light_medium_battery|torpedo)_1[ \t]*\r?\n?',
                    '', t)
    assert n == 2, f'{tag}: MOT 船变体槽删除数 {n}'
    save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'{tag}: MOT 风车菊级/蒲公英级 删除无效槽 ×{n} ✓')

    # 3) DVA 部队
    p = os.path.join(base, 'history', 'units', 'DVA_1936.txt')
    if tag == '仓库':
        shutil.copy2(p, os.path.join(BD, 'DVA_1936.txt'))
    raw, t = load(p)
    t2, n = re.subn(r'(?m)^([ \t]*location[ \t]*=[ \t]*)2463\b', r'\g<1>442', t)
    assert n == len(re.findall(r'(?m)^\s*location\s*=', t)), f'{tag}: DVA location 替换 {n}'
    save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'{tag}: DVA 部队 location 2463→442 ×{n} ✓')

print()
print('=== 验证 ===')
for tag, base in COPIES:
    t = open(os.path.join(base, 'common', 'on_actions', 'DOT_on_actions.txt'), encoding='utf-8-sig').read()
    print(f'  {tag}: 26型底盘={"CAS ✓" if "small_plane_cas_airframe_0" in t else "✗"}')
    t = open(os.path.join(base, 'history', 'countries', 'MOT - Mondstadt.txt'), encoding='utf-8-sig').read()
    print(f'  {tag}: MOT 无效槽残留={len(re.findall(chr(102)+"ront_1_custom_slot" + chr(32)*0, t)) if False else sum(1 for l in t.splitlines() if "front_1_custom_slot" in l and "ship_" in l and ("light_medium_battery_1" in l or "torpedo_1" in l))}')
    t = open(os.path.join(base, 'history', 'units', 'DVA_1936.txt'), encoding='utf-8-sig').read()
    print(f'  {tag}: DVA 2463 残留={t.count("2463")}，442 出现={t.count("= 442")}')

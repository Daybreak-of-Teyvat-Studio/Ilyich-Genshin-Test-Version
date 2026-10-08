# -*- coding: utf-8 -*-
"""fix_hero_trigger.py —— 把 has_full_control_of = PREV 修成正确的 has_full_control_of_state = PREV
应用到仓库 + 已部署副本两处"""
import sys

sys.stdout.reconfigure(encoding='utf-8')
paths = [
    r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\events\Ilyich_Hero_Event.txt',
    r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version\events\Ilyich_Hero_Event.txt',
]
for p in paths:
    raw = open(p, 'rb').read()
    n = raw.count(b'has_full_control_of = PREV')
    raw2 = raw.replace(b'has_full_control_of = PREV', b'has_full_control_of_state = PREV')
    open(p, 'wb').write(raw2)
    tag = '仓库' if 'GitHub' in p else '副本'
    print(f'{tag}: 替换 {n} 处；残留坏写法 {raw2.count(b"has_full_control_of =")}；'
          f'好写法 {raw2.count(b"has_full_control_of_state =")}')

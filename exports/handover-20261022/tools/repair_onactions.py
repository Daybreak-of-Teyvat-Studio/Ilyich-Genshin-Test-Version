# -*- coding: utf-8 -*-
"""repair_onactions.py —— 修复 DOT_on_actions.txt 的闲云机-26型替换（括号平衡提取重做）
仓库+副本；从备份复原后用平衡括号法重做替换"""
import os, re, sys, glob, shutil

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
BD = sorted(glob.glob(os.path.join(ROOT, '.backups', 'equipfix_*')))[-1]
orig = open(os.path.join(BD, 'DOT_on_actions.txt'), 'rb').read()

NEW26 = ('create_equipment_variant = {\r\n'
         '\t\t\t\t\tname = "\u95f2\u4e91\u673a-26\u578b"\r\n'
         '\t\t\t\t\ttype = small_plane_cas_airframe_0\r\n'
         '\t\t\t\t\tmodules = {\r\n'
         '\t\t\t\t\t\tfixed_main_weapon_slot = bomb_locks\r\n'
         '\t\t\t\t\t\tengine_type_slot = engine_1_1x\r\n'
         '\t\t\t\t\t\tspecial_type_slot_1 = empty\r\n'
         '\t\t\t\t\t}\r\n'
         '\t\t\t\t\ticon = GFX_antiair5_medium\r\n'
         '\t\t\t\t}')

for tag, base in COPIES:
    p = os.path.join(base, 'common', 'on_actions', 'DOT_on_actions.txt')
    t = orig.decode('utf-8-sig')
    # 平衡括号提取 闲云机-26型 的整个变体块
    pat = re.compile(r'create_equipment_variant\s*=\s*\{')
    m = pat.search(t)
    done = False
    while m and not done:
        if '\u95f2\u4e91\u673a-26\u578b' in t[m.start():m.start() + 200]:
            depth, i = 0, m.end() - 1
            while i < len(t):
                if t[i] == '{':
                    depth += 1
                elif t[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            t = t[:m.start()] + NEW26 + t[i + 1:]
            done = True
        else:
            m = pat.search(t, m.end())
    assert done, f'{tag}: 未找到 26型'
    open(p, 'wb').write(((b'\xef\xbb\xbf' if orig[:3] == b'\xef\xbb\xbf' else b'') + t.encode('utf-8')))
    print(f'{tag}: 重做替换完成')

print()
print('=== 验证 ===')
for tag, base in COPIES:
    p = os.path.join(base, 'common', 'on_actions', 'DOT_on_actions.txt')
    t = open(p, encoding='utf-8-sig').read()
    depth = 0
    for ch in t:
        depth += (ch == '{') - (ch == '}')
    print(f'  {tag}: 括号平衡={depth == 0}，CAS底盘={"✓" if "small_plane_cas_airframe_0" in t else "✗"}，'
          f'26型块数={len(re.findall(chr(50)+"6" + chr(0x578b), t))}')

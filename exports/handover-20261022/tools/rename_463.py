# -*- coding: utf-8 -*-
"""rename_463.py —— s463 苔骨荒原 → 刻拉蒂之眼（幂等，含备份与回读验证）"""
import os, re, sys, shutil

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'localisation', 'simp_chinese',
                 'DOT_state_names_gamma_l_simp_chinese.yml')
BD = os.path.join(ROOT, '.backups', 'name463_20261007')
os.makedirs(BD, exist_ok=True)
shutil.copy2(P, BD)

raw = open(P, 'rb').read()
t = raw.decode('utf-8-sig')
t2, n = re.subn(r'(DOT_STATE_463:0\s*)"苔骨荒原"', r'\g<1>刻拉蒂之眼'.replace('刻', '"刻', 1) if False else r'\g<1>"刻拉蒂之眼"', t)
if n == 0 and 'DOT_STATE_463:0 "刻拉蒂之眼"' in t:
    print('已是目标名，幂等跳过')
    n = 0
else:
    open(P, 'wb').write(((b'\xef\xbb\xbf' if raw[:3] == b'\xef\xbb\xbf' else b'') + t2.encode('utf-8')))
    print(f'替换 {n} 处')

t3 = open(P, encoding='utf-8-sig').read()
m = re.search(r'DOT_STATE_463:0\s*"([^"]*)"', t3)
print('s463 现名:', m.group(1))
assert m.group(1) == '刻拉蒂之眼', '验证失败'
print('✓')

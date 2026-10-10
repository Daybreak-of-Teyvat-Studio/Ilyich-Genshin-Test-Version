# -*- coding: utf-8 -*-
"""fix_deploy_crlf.py —— 副本 DOT_on_actions 行尾修复 + 双副本/括号终验"""
import os, sys, hashlib, subprocess

sys.stdout.reconfigure(encoding='utf-8')
cur = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version\common\on_actions\DOT_on_actions.txt'
r = open(cur, 'rb').read()
t = r
if t[:3] == b'\xef\xbb\xbf':
    t = t[3:]
t = t.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
open(cur, 'wb').write(t)
r2 = open(cur, 'rb').read()
print('副本修复后: BOM=', r2[:3] == b'\xef\xbb\xbf', 'CRLF=', r2.count(b'\r\n'))

repo = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
print()
print('=== 三个今天修复的文件 两边一致性 ===')
for rel in ('common/on_actions/DOT_on_actions.txt', 'history/countries/MOT - Mondstadt.txt',
            'history/units/DVA_1936.txt'):
    a = open(os.path.join(repo, *rel.split('/')), 'rb').read()
    b = open(os.path.join('C:\\Users\\LR\\Documents\\Paradox Interactive\\Hearts of Iron IV\\mod\\Daybreak of Teyvat Gamma Version', *rel.split('/')), 'rb').read()
    print(f'  {rel}: {"✓ 一致" if hashlib.md5(a).hexdigest() == hashlib.md5(b).hexdigest() else "✗ 不一致"}')

print()
r = subprocess.run([sys.executable, '-X', 'utf8',
                    r'C:\Users\LR\.zcode\skills\hoi4-modder-cn\scripts\check_brackets.py',
                    '--mod', repo], capture_output=True, text=True, encoding='utf-8')
print('括号自检:', (r.stdout or '').strip()[-40:])

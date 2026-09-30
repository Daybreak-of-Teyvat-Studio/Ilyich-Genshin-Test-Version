# -*- coding: utf-8 -*-
"""补上 state 466 = 蒙德城"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')

cur = open(SN, encoding='utf-8-sig', errors='replace').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
print(f'写入前 state 466 的名字: 「{names.get(466)}」')
assert 466 in names, 'state 466 不在本地化文件里'

bdir = os.path.join(ROOT, '.backups', 'name466_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))

names[466] = '蒙德城'
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
raw = open(SN, 'rb').read()
print(f'已写入  state 466 = 蒙德城')
print(f'  BOM={raw[:3] == b"\xef\xbb\xbf"}  CRLF={raw.count(bytes([13,10]))}  条数=${len(names)}')

# 复验 + 列出全部具名
txt = open(SN, encoding='utf-8-sig', errors='replace').read()
v = dict((int(m.group(1)), m.group(2)) for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', txt, re.M))
named = {k: x for k, x in v.items() if x != '*'}
print(f'\n=== 全部具名州 {len(named)} 个 ===')
for k in sorted(named):
    p = os.path.join(ST, f'{k}-State_{k}.txt')
    own = None
    if os.path.exists(p):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        mo = re.search(r'\bowner\s*=\s*(\w+)', t)
        own = mo.group(1) if mo else None
        ps = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
    else:
        ps = []
    print(f'  state {k:5d}（{own}）: 「{named[k]}」  {len(ps)} 省')
print(f'\n备份 {bdir}')

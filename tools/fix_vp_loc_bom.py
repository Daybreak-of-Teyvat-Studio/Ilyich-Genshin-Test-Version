# -*- coding: utf-8 -*-
"""fix_vp_loc_bom.py —— 给 simp_chinese 全部本地化 yml 补 BOM（幂等）"""
import os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOC = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'localisation')
fixed, ok = [], 0
for p in glob.glob(os.path.join(LOC, '**', '*.yml'), recursive=True):
    raw = open(p, 'rb').read()
    if raw[:3] == b'\xef\xbb\xbf':
        ok += 1
        continue
    open(p, 'wb').write(b'\xef\xbb\xbf' + raw)
    fixed.append(os.path.relpath(p, LOC))
print(f'BOM 正常: {ok} 个')
print(f'补了 BOM: {len(fixed)} 个')
for f in fixed:
    print('  ' + f)

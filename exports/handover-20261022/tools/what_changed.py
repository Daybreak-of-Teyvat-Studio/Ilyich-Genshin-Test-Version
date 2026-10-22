# -*- coding: utf-8 -*-
"""what_changed.py —— 找出部署副本中 10-08 11:22 之后变动的文件 + 仓库/副本差异"""
import os, sys, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
CUT = datetime.datetime(2026, 10, 8, 11, 22).timestamp()
SKIP = {'.backups', '.backup', '__pycache__'}

print('=== 部署副本中 10-08 11:22 之后修改的文件 ===')
n = 0
for dp, dn, fn in os.walk(DEP):
    dn[:] = [d for d in dn if d not in SKIP]
    for f in fn:
        p = os.path.join(dp, f)
        try:
            m = os.path.getmtime(p)
        except OSError:
            continue
        if m > CUT:
            n += 1
            sz = os.path.getsize(p)
            print(f'  {os.path.relpath(p, DEP)}  {sz}B  {datetime.datetime.fromtimestamp(m)}')
            if n > 60:
                print('  ...')
                break
    if n > 60:
        break
print(f'共 {n} 个')

print()
print('=== 仓库 vs 副本 差异（大小比较） ===')
tr, td = {}, {}
for base, tree in ((REPO, tr), (DEP, td)):
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            p = os.path.join(dp, f)
            tree[os.path.relpath(p, base)] = os.path.getsize(p)
only_r = sorted(set(tr) - set(td))
only_d = sorted(set(td) - set(tr))
diff = [k for k in set(tr) & set(td) if tr[k] != td[k]]
print(f'只在仓库: {len(only_r)}；只在副本: {len(only_d)}；大小不同: {len(diff)}')
for k in only_r[:10]:
    print('  R only:', k)
for k in only_d[:10]:
    print('  D only:', k)
for k in diff[:10]:
    print(f'  differ: {k}  R={tr[k]} D={td[k]}')

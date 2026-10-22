# -*- coding: utf-8 -*-
"""compare_copies.py —— 对比仓库 Gamma 与 Documents 副本（目录树级差异）"""
import os, sys, hashlib

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

SKIP = {'.backups', '.backup', '.git', '__pycache__'}


def tree(base):
    out = {}
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, base)
            out[rel] = os.path.getsize(p)
    return out


tr, td = tree(R), tree(D)
only_r = sorted(set(tr) - set(td))
only_d = sorted(set(td) - set(tr))
diff = sorted(k for k in set(tr) & set(td) if tr[k] != td[k])
print(f'仓库 {len(tr)} 个文件，副本 {len(td)} 个文件')
print(f'只在仓库: {len(only_r)}')
for k in only_r[:25]:
    print('  R:', k)
print(f'只在副本: {len(only_d)}')
for k in only_d[:25]:
    print('  D:', k)
print(f'同名不同大小: {len(diff)}')
for k in diff[:25]:
    print(f'  ! {k}: R={tr[k]} D={td[k]}')

# strategicregions / supplyareas 专查
for sub in ('map\\strategicregions', 'map\\supplyareas'):
    pr, pd_ = os.path.join(R, sub), os.path.join(D, sub)
    nr = len(os.listdir(pr)) if os.path.isdir(pr) else -1
    nd = len(os.listdir(pd_)) if os.path.isdir(pd_) else -1
    print(f'{sub}: 仓库 {nr} 个文件, 副本 {nd} 个')

# -*- coding: utf-8 -*-
"""verify_swap_diff.py —— 用部署副本（未动）当快照，核对仓库已做的换位改动
+ 找出所有非 UTF-8 的 .txt 文件"""
import os, sys, glob, hashlib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
SKIP = {'.backups', '.backup', '__pycache__'}

def tree(base):
    out = {}
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, base)] = hashlib.md5(open(p, 'rb').read()).hexdigest()
    return out

print('哈希中...')
tr, td = tree(REPO), tree(DEP)
diff = sorted(k for k in set(tr) & set(td) if tr[k] != td[k])
only_r = sorted(set(tr) - set(td))
only_d = sorted(set(td) - set(tr))
print(f'仓库 vs 副本（副本=换位前快照）: 内容不同 {len(diff)}，只在仓库 {len(only_r)}，只在副本 {len(only_d)}')
for k in diff:
    print('  differ:', k)
for k in only_d[:10]:
    print('  D only:', k)

# 检查"被重存的 62 个首都文件"是否真的内容没变（随机抽 5 个比对 md5）
print()
print('抽检首都文件（应内容未变）——若上面差分为空则全部未变')

# 非 UTF-8 文件扫描
print()
print('=== 非 UTF-8 的 .txt 文件 ===')
bad = []
for dp, dn, fn in os.walk(REPO):
    dn[:] = [d for d in dn if d not in SKIP]
    for f in fn:
        if not f.endswith(('.txt', '.yml', '.csv')):
            continue
        p = os.path.join(dp, f)
        raw = open(p, 'rb').read()
        try:
            raw.decode('utf-8-sig')
        except UnicodeDecodeError as e:
            bad.append((os.path.relpath(p, REPO), str(e)[:60]))
for b in bad[:30]:
    print(' ', b)
print(f'共 {len(bad)} 个')

# -*- coding: utf-8 -*-
"""仓库 mod 与本地部署 mod 全树对照"""
import os, io, sys, hashlib, collections
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
o = []

def tree(root):
    d = {}
    for dp, dn, fn in os.walk(root):
        for f in fn:
            fp = os.path.join(dp, f)
            rel = os.path.relpath(fp, root).lower()
            try:
                d[rel] = (os.path.getsize(fp), fp)
            except OSError:
                pass
    return d

a, b = tree(REPO), tree(DEPL)
o.append(f'仓库文件数 {len(a)}, 副本文件数 {len(b)}')
only_a = sorted(set(a) - set(b))
only_b = sorted(set(b) - set(a))
o.append(f'仅仓库有 ({len(only_a)}): {only_a[:30]}')
o.append(f'仅副本有 ({len(only_b)}): {only_b[:30]}')

diff_size = sorted(k for k in set(a) & set(b) if a[k][0] != b[k][0])
o.append(f'大小不同 ({len(diff_size)}):')
for k in diff_size[:40]:
    o.append(f'  {k}: 仓库 {a[k][0]}B / 副本 {b[k][0]}B')

# 同大小的抽样哈希（只对 <2MB 的文件，全量哈希太大）
same = [k for k in set(a) & set(b) if k not in diff_size and a[k][0] < 2 * 1024 * 1024]
n_hash = 0
for k in same[:20000]:
    ha = hashlib.md5(io.open(a[k][1], 'rb').read()).hexdigest()
    hb = hashlib.md5(io.open(b[k][1], 'rb').read()).hexdigest()
    n_hash += 1
    if ha != hb:
        o.append(f'  内容不同(同大小): {k}')
o.append(f'同大小哈希抽检 {n_hash} 个')
io.open(os.path.join(REPO, '..', 'tools', 'copydrift_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

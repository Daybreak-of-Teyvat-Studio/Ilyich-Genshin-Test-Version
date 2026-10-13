# -*- coding: utf-8 -*-
"""analyze_new_log.py —— ①新日志地图类逐类型明细 ②海军变体现状 ③撤掉 328 海州行(--apply)"""
import os, re, sys, glob, shutil, datetime, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'revert_sea_{stamp}')
os.makedirs(BD, exist_ok=True)

t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]

print('=' * 66)
print('【①】328 条 :716 的逐类型明细（谁落在外州）')
c = collections.Counter()
for l in lines:
    m = re.search(r'mapbuildings\.cpp:716\]: map/buildings\.txt error at line (\d+): map building\((.*?)\) location', l)
    if m:
        c[m.group(2)] += 1
for k, n in c.most_common():
    print(f'  {k}: {n}')
print(f'  总计 {sum(c.values())}')

print()
print('【②】海军变体在本次运行的状态')
for pat, name in ((r'equipmentpool\.cpp:1410', 'equipmentpool(舰)'),
                  (r'equipmentvariant\.cpp:1112', 'equipmentvariant(名称)')):
    hits = [l.strip() for l in lines if re.search(pat, l)]
    cc = collections.Counter()
    for l in hits:
        m = re.search(r'Country "(\w+)" does not have any equipment variant for type "(\w+)"', l)
        if m:
            cc[(m.group(1), m.group(2))] += 1
    print(f'  {name}: {len(hits)} 条 -> {dict(cc)}')

print()
print('【③】撤掉 328 条海州行（--apply 生效）')
for tag, base in (('仓库', G), ('副本', D)):
    p = os.path.join(base, 'map', 'buildings.txt')
    t2 = open(p, encoding='utf-8-sig', errors='replace').read()
    ls = t2.split('\n')
    # 海州 id 集合（709-717, 719-750）
    sea = set(range(709, 718)) | set(range(719, 751))
    keep, drop = [], []
    for l in ls:
        c2 = l.split(';')
        if len(c2) >= 7 and c2[0].strip().isdigit() and int(c2[0]) in sea:
            drop.append(l)
        else:
            keep.append(l)
    print(f'  {tag}: 找到海州行 {len(drop)} 条（期望 328）')
    out = '\r\n'.join([x for x in keep if x.strip()]) + '\r\n'
    out = out.rstrip(b'\r\n' if isinstance(out, bytes) else '\r\n')  # 结尾不带换行
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_buildings.txt'))
        open(p, 'wb').write(out.encode('utf-8'))
print(f'模式: {"已应用" if APPLY else "DRY"}  备份: {BD}')

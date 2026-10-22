# -*- coding: utf-8 -*-
"""hunt_missing_states.py —— 全树找 707/708/709 的内容下落 + 现况 id 集核查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

print('=== ① 两副本当前 id 集与缺号 ===')
for tag, base in (('仓库', G), ('副本', D)):
    d = os.path.join(base, 'history', 'states')
    ids = []
    for f in glob.glob(os.path.join(d, '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
        if m:
            ids.append(int(m.group(1)))
    ids = sorted(ids)
    gaps = [i for i in range(1, max(ids) + 1) if i not in set(ids)]
    print(f'  {tag}: {len(ids)} 个, id {min(ids)}-{max(ids)}, 缺号 {gaps}')

print()
print('=== ② 全 mod 树搜 "id = 707/708/709" 的文件（含非 states 目录）===')
for tag, base in (('仓库', G),):
    for root2, dirnames, filenames in os.walk(base):
        if '.backups' in root2:
            continue
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(root2, fn)
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            m = re.search(r'(?m)^\s*id\s*=\s*(70[789])\s*$', t)
            if m and 'state = {' in t:
                print(f'  {os.path.relpath(fp, base)}: id={m.group(1)}')

print()
print('=== ③ 全 .backups 搜含 DOT_STATE_707/708/709 的备份文件 ===')
bd = os.path.join(ROOT, '.backups')
hit = 0
for root2, dirnames, filenames in os.walk(bd):
    for fn in filenames:
        if not fn.endswith('.txt'):
            continue
        fp = os.path.join(root2, fn)
        t = open(fp, encoding='utf-8-sig', errors='replace').read()
        for sid in ('707', '708', '709'):
            if f'DOT_STATE_{sid}"' in t and 'state = {' in t:
                print(f'  {os.path.relpath(fp, bd)}: 含 DOT_STATE_{sid}')
                hit += 1
if not hit:
    print('  （无）')

print()
print('=== ④ 23:43 被改文件的抽查（94/110/186 的当前头部）===')
for sid in (94, 110, 186):
    fs = glob.glob(os.path.join(G, 'history', 'states', f'{sid}*.txt'))
    fs = [f for f in fs if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    if fs:
        t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
        head = [l for l in t.split('\n')[:6]]
        print(f'  --- {os.path.basename(fs[0])} ---')
        for l in head:
            print('   ', l.strip()[:110])

print()
print('=== ⑤ 除 states 外，全盘搜 "分道誓约" 与 "回声之子" ===')
for kw in ('分道誓约', '回声之子'):
    for root2, dirnames, filenames in os.walk(ROOT):
        if '.backups' in root2 or '.git' in root2:
            continue
        for fn in filenames:
            if not fn.endswith(('.txt', '.yml', '.md')):
                continue
            fp = os.path.join(root2, fn)
            try:
                t = open(fp, encoding='utf-8-sig', errors='replace').read()
            except Exception:
                continue
            if kw in t:
                print(f'  [{kw}] {os.path.relpath(fp, ROOT)}')

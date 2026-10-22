# -*- coding: utf-8 -*-
"""回滚 5 处飞地迁移：从 enclave_same_20260927_175554 还原 10 个州文件。"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
ST = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')
BK = os.path.join(ROOT, '.backups', 'enclave_same_20260927_175554')

files = sorted(os.listdir(BK))
print(f'从 {BK} 还原 {len(files)} 个州文件')
# 先把当前状态另存，便于再次对比
safety = os.path.join(ROOT, '.backups', 'pre_rollback_' +
                      datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(safety, exist_ok=True)

ok = 0
for f in files:
    cur = os.path.join(ST, f)
    if os.path.exists(cur):
        shutil.copy2(cur, os.path.join(safety, f))
    shutil.copy2(os.path.join(BK, f), cur)
    ok += 1
print(f'已还原 {ok} 个文件；还原前状态另存 {safety}')

# 复验：当前 == 备份
bad = []
for f in files:
    b = open(os.path.join(BK, f), encoding='utf-8-sig', errors='replace').read()
    c = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    if b != c:
        bad.append(f)
print(f'复验 当前==备份: {len(files) - len(bad)}/{len(files)}  {bad}')

print()
print('=== 还原后各州省列表 ===')
for f in files:
    sid = int(re.match(r'(\d+)-', f).group(1))
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    ps = sorted(int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split())
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    print(f'  state {sid:3d}({mo.group(1) if mo else "海州"}): {len(ps):2d} 省 {ps}')

print()
print('=== 5 个省现在的归属（应回到原位）===')
s2p = {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for p in re.findall(r'\d+', re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1)):
        s2p[int(p)] = sid
for p, expect in [(3499, 54), (4686, 74), (2643, 203), (461, 514), (1154, 529)]:
    got = s2p.get(p)
    print(f'  省 {p}: 现在 state {got}（应为 {expect}）{"✓" if got == expect else "✗"}')

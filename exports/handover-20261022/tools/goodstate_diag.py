# -*- coding: utf-8 -*-
"""goodstate_diag.py —— IsMapInGoodState / 战略区域覆盖 / no state 全查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'

print('=' * 70)
print('【A】当前 error.log 里的 goodstate / strategic region / no state 类')
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
PAT = re.compile(r'(?i)(good ?state|strategic ?region|no state|missing state|not in a state|has no strategic|IsMapInGoodState)')
hits = [l.strip() for l in t.split('\n') if PAT.search(l)]
print(f'  命中 {len(hits)} 行:')
for l in hits[:60]:
    print('  ', l[:230])
if not hits:
    print('  （无）')

print()
print('=' * 70)
print('【B】game.log 里的 goodstate 类')
t2 = open(os.path.join(L, 'game.log'), encoding='utf-8-sig', errors='replace').read()
for l in t2.split('\n'):
    if PAT.search(l) or 'is in good state' in l.lower():
        print('  ', l.strip()[:230])

print()
print('=' * 70)
print('【C】战略区域文件覆盖分析')
sr_dir = os.path.join(G, 'map', 'strategicregions')
prov_in_regions = set()
n_regions = 0
for f in glob.glob(os.path.join(sr_dir, '*.txt')):
    t3 = open(f, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'provinces\s*=\s*\{', t3):
        depth, i = 0, m.end() - 1
        while i < len(t3):
            if t3[i] == '{':
                depth += 1
            elif t3[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blk = t3[m.end():i]
        for pid in re.findall(r'\d+', blk):
            prov_in_regions.add(int(pid))
    n_regions += len(re.findall(r'(?m)^\s*strategic_region\s*=\s*\{', t3))
    print(f'  {os.path.basename(f)}: {(os.path.getsize(f)):,}B')

# definition 全量
gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = c[4]
        except ValueError:
            pass

all_ids = set(gk)
missing = sorted(all_ids - prov_in_regions)
print(f'  区域文件声明省数: {len(prov_in_regions)}（去重后）')
print(f'  definition 省数: {len(all_ids)}')
print(f'  ★未被任何战略区域收录的省: {len(missing)} 个')
if missing:
    print(f'    前 40: {missing[:40]}')
    # 按 kind 统计
    import collections
    c2 = collections.Counter(gk.get(p) for p in missing)
    print(f'    kind 分布: {dict(c2)}')
else:
    print('    全覆盖 ✓')

print()
print('=' * 70)
print('【D】省→州 覆盖（有省不属于任何州？）')
prov2state = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t4 = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t4)
    if m:
        for pid in re.findall(r'\d+', m.group(1)):
            prov2state.setdefault(int(pid), True)
nostate = sorted(all_ids - set(prov2state))
print(f'  不属于任何州的省: {len(nostate)} 个')
if nostate:
    print(f'    前 30: {nostate[:30]}')
    import collections
    c3 = collections.Counter(gk.get(p) for p in nostate)
    print(f'    kind: {dict(c3)}')

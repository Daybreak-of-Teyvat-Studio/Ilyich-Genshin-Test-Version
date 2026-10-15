import os, io, re, shutil, datetime, glob

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK = os.path.join(REPO, '.backups', 'mega014_20261014_220448')
OUT = os.path.join(REPO, 'tools', 'regtest_out.txt')
o = []

# 0) 先看 colors.txt / weatherpositions 结构（只读）
gt = os.path.join(G, 'map', 'colors.txt')
if os.path.exists(gt):
    t = io.open(gt, 'rb').read().decode('utf-8-sig', errors='replace')
    o.append(f'===== colors.txt ({len(t)} 字符) 前 45 行 =====')
    for l in t.splitlines()[:45]:
        o.append('  ' + l[:180])
    o.append(f'  ... 含 "46" 的行: {[l.strip()[:80] for l in t.splitlines() if re.search(r"\\b46\\b", l)][:8]}')
    o.append(f'  含 "strategic" 的行: {[l.strip()[:80] for l in t.splitlines() if "strateg" in l.lower()][:8]}')
o.append('')
wp = os.path.join(G, 'map', 'weatherpositions.txt')
t = io.open(wp, 'rb').read().decode('utf-8-sig', errors='replace')
o.append('===== weatherpositions.txt 全文 =====')
o.append('  ' + repr(t))
o.append('')

# 1) 备份当前战略区文件
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bd = os.path.join(REPO, '.backups', f'regtest_{stamp}')
os.makedirs(bd, exist_ok=True)
for label, root in [('repo', G), ('depl', DEPL)]:
    for f in ('DOT_Strategicregions_01.txt', 'DOT_Strategicregions_46.txt'):
        src = os.path.join(root, 'map', 'strategicregions', f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(bd, f'{label}_{f}'))
o.append(f'已备份当前战略区 → {bd}')

# 2) 回退区域1（用 mega014 备份），删除区域46
src1 = os.path.join(BK, '仓库_r1_DOT_Strategicregions_01.txt')
src1b = os.path.join(BK, '副本_r1_DOT_Strategicregions_01.txt')
o.append(f'备份里区域1: 仓库={os.path.exists(src1)}, 副本={os.path.exists(src1b)}')
for dst, s in [(os.path.join(G, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt'), src1),
               (os.path.join(DEPL, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt'), src1b)]:
    shutil.copy2(s, dst)
    tt = io.open(dst, 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'provinces=\{([^}]*)\}', tt, re.S)
    n = len(m.group(1).split()) if m else -1
    o.append(f'  区域1 已回退: {os.path.dirname(dst)} 省数={n}')

for root in (G, DEPL):
    fp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_46.txt')
    if os.path.exists(fp):
        os.remove(fp)
        o.append(f'  已删除区域46: {root}')
    left = os.listdir(os.path.join(root, 'map', 'strategicregions'))
    o.append(f'  剩余战略区文件: {left}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

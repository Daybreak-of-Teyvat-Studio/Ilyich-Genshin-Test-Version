import os, io, re, collections

LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups\mega014_20261014_220448'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\crash1042_out.txt'
o = []

# ===== 1) 新 error.log =====
ep = os.path.join(LOGS, 'error.log')
le = io.open(ep, 'rb').read().decode('utf-8-sig', errors='replace').splitlines()
o.append(f'===== error.log: {len(le)} 行 =====')
o.append(f'首行: {le[0][:160]}')
o.append(f'末行时间戳区域: {le[-1][:60]}')

pats = {
    '马斯克海/温度': r'马斯克海|temperature doesn',
    'MAP_ERROR': r'MAP_ERROR',
    'BUILDING IGNORED': r'BUILDING IGNORED',
    'not within specified state': r'not within specified state',
    'not over the land': r'not over the land',
    'no air base site': r'no air base site',
    'no rocket site': r'no rocket site',
    'no gun emplacement': r'no gun emplacement',
    'strategicregion': r'strategicregion',
    'X crossing': r'X crossing',
    'no provinces in state': r'no provinces in state',
    'Missing State': r'Missing [Ss]tate',
    'state.cpp': r'state\.cpp',
    'buildings.txt error': r'buildings\.txt',
}
o.append('')
o.append('--- 关键模式计数 + 前 10 条样例 ---')
for name, pat in pats.items():
    rx = re.compile(pat)
    hits = [(i + 1, l) for i, l in enumerate(le) if rx.search(l)]
    o.append(f'[{len(hits):4d}] {name}')
    for ln, l in hits[:10]:
        o.append(f'      L{ln}: {l.strip()[:200]}')

# 尾部 40 行
o.append('')
o.append('--- 尾部 40 行 ---')
for i, l in enumerate(le[-40:], len(le) - 39):
    o.append(f'L{i}: {l.rstrip()[:200]}')

# ===== 2) 新 crash 目录 =====
CR = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\crashes\hoi4_20261015_104225')
o.append('')
o.append('===== 新 crash exception.txt =====')
try:
    t = io.open(os.path.join(CR, 'exception.txt'), 'rb').read().decode('utf-8', errors='replace')
    o.append(t)
except Exception as e:
    o.append(str(e))

# ===== 3) buildings.txt col1 分布对比 =====
def col1_counts(fp):
    c = collections.Counter()
    rows = []
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for l in t.split('\n'):
        l = l.rstrip('\r')
        if not l.strip():
            continue
        parts = l.split(';')
        if not parts[0].strip().isdigit():
            continue
        c[int(parts[0])] += 1
        if int(parts[0]) in (62, 63, 65, 66, 67, 703, 704, 705, 706):
            rows.append(l)
    return c, rows

o.append('')
o.append('===== buildings.txt col1 对比 =====')
cur_fp = os.path.join(REPO, 'map', 'buildings.txt')
cc, crou = col1_counts(cur_fp)
o.append(f'当前文件: {sum(cc.values())} 行')
for s in (62, 63, 65, 66, 67, 703, 704, 705, 706):
    o.append(f'  col1={s}: {cc.get(s, 0)} 行')

bkr = [f for f in os.listdir(BK)] if os.path.isdir(BK) else []
o.append(f'备份目录内容: {bkr}')

bk_bld = os.path.join(BK, 'buildings.txt')
if os.path.exists(bk_bld):
    bc, brow = col1_counts(bk_bld)
    o.append(f'备份文件: {sum(bc.values())} 行')
    for s in (62, 63, 65, 66, 67, 703, 704, 705, 706):
        o.append(f'  col1={s}: {bc.get(s, 0)} 行')
else:
    # 找备份里的 buildings
    cand = []
    for root, dirs, files in os.walk(BK):
        for f in files:
            if 'buildings' in f.lower():
                cand.append(os.path.join(root, f))
    o.append(f'备份内 buildings 候选: {cand}')

# 备份中 63/65/66/67 行样例
o.append('')
o.append('--- 备份中 col1∈{63,65,66,67} 的行（前 40） ---')
if os.path.exists(bk_bld):
    for l in brow:
        p = l.split(';')
        if p[0].strip() in ('63', '65', '66', '67'):
            o.append(f'  {l[:150]}')

o.append('')
o.append('--- 当前中 col1∈{62,63,65,66,67} 的行（前 60） ---')
for l in crou:
    p = l.split(';')
    if p[0].strip() in ('62', '63', '65', '66', '67'):
        o.append(f'  {l[:150]}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok', len(o))

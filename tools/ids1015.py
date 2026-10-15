import os, io, re

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\ids1015_out.txt'
o = []

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    sd = os.path.join(root, 'history', 'states')
    o.append(f'===== {label} {sd} =====')
    files = [f for f in os.listdir(sd) if f.endswith('.txt')]
    bad_id, bad_name, bad_empty, ids = [], [], [], []
    for fn in files:
        m = re.match(r'^(\d+)-State_\1\.txt$', fn)
        if not m:
            o.append(f'  ⚠ 非标准文件名: {fn}')
            continue
        n = int(m.group(1))
        ids.append(n)
        fp = os.path.join(sd, fn)
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        lines = t.splitlines()
        idl = None
        for l in lines[:6]:
            mm = re.match(r'\s*id\s*=\s*(\d+)', l)
            if mm:
                idl = int(mm.group(1))
                break
        if idl != n:
            bad_id.append((fn, idl))
        namel = None
        for l in lines[:6]:
            mm = re.search(r'name\s*=\s*"(DOT_STATE_\d+)"', l)
            if mm:
                namel = mm.group(1)
                break
        if namel != f'DOT_STATE_{n}':
            bad_name.append((fn, namel))
        # provinces 非空
        mp = re.search(r'provinces\s*=\s*\{', t)
        if mp:
            seg = t[mp.end():mp.end()+200]
            if '}' in seg and not re.search(r'\d', seg[:seg.index('}')]):
                bad_empty.append(fn)
    ids_set = set(ids)
    holes = [i for i in range(1, max(ids)+1) if i not in ids_set]
    dups = [i for i in ids_set if ids.count(i) > 1]
    o.append(f'  文件数 {len(files)}, max={max(ids)}, 缺号={holes if holes else "无"}, 重号={dups if dups else "无"}')
    o.append(f'  id 行不符: {bad_id if bad_id else "无"}')
    o.append(f'  name key 不符: {bad_name if bad_name else "无"}')
    o.append(f'  空 provinces: {bad_empty if bad_empty else "无"}')
    o.append('')

# 62/63/65/66/67 全文（仓库）
sd = os.path.join(REPO, 'history', 'states')
for n in (62, 63):
    fp = os.path.join(sd, f'{n}-State_{n}.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    o.append(f'===== 仓库 {n}-State_{n}.txt 全文（{len(t)} 字符） =====')
    o.append(t)
    o.append('')

# 65/66/67 头部 12 行 + id/name/provinces
for n in (65, 66, 67):
    fp = os.path.join(sd, f'{n}-State_{n}.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    o.append(f'===== 仓库 {n}-State_{n}.txt 前 12 行 =====')
    for i, l in enumerate(t.splitlines()[:12]):
        o.append(f'  {i+1}: {l[:150]}')
    o.append('')

# 区域46 原始字节（行尾风格）
fp = os.path.join(REPO, 'map', 'strategicregions', 'DOT_Strategicregions_46.txt')
raw = io.open(fp, 'rb').read()
o.append(f'===== 区域46 原始字节（{len(raw)}B） =====')
o.append(repr(raw))

# 区域1 weather 块原文（用于复制）
fp1 = os.path.join(REPO, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt')
t1 = io.open(fp1, 'rb').read().decode('utf-8-sig', errors='replace')
i = t1.find('\tweather=')
o.append('')
o.append(f'===== 区域1 weather 块（从字符 {i} 到结尾，共 {len(t1)-i} 字符） =====')
o.append(repr(t1[i:]))

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok', len(o))

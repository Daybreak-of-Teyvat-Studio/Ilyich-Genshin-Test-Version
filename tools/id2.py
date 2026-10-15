import os, io, re, glob

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
OUT = os.path.join(REPO, 'tools', 'id2_out.txt')
o = []

# 查 loc 里 02 与 46 的名字 + 检查 mod 是否别处引用战略区 id
locf = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Strategic_Region_Names_l_simp_chinese.yml')
if os.path.exists(locf):
    t = io.open(locf, 'rb').read().decode('utf-8-sig', errors='replace')
    for k in ('DOT_STRATEGICREGIONS_01', 'DOT_STRATEGICREGIONS_02', 'DOT_STRATEGICREGIONS_03', 'DOT_STRATEGICREGIONS_46'):
        for l in t.splitlines():
            if k + ':' in l:
                o.append(f'loc {k}: {l.strip()[:100]}')
o.append('')
o.append('mod 内引用 strategic_region 的文件:')
hits = []
for root2, dirs2, files2 in os.walk(G):
    if any(x in root2 for x in ('.git', '.backups', 'map', 'gfx', 'localisation')):
        continue
    for f in files2:
        if f.endswith('.txt'):
            fp = os.path.join(root2, f)
            tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
            if 'strategic_region' in tt:
                hits.append(os.path.relpath(fp, G))
o.append(f'  {hits if hits else "无"}')

# 改 id 46 → 2（保留 name 键 DOT_STRATEGICREGIONS_46，显示名=马斯克海）
o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_46.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig')
    t2 = re.sub(r'(\bid\s*=\s*)46', r'\g<1>2', t, count=1)
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig')
    o.append(f'{label} 区域46文件已改 id=2:')
    for l in chk.splitlines()[:4]:
        o.append('   ' + l)
    # 文件名也改成 02（引擎按目录读取，文件名不影响；便于人工辨认）
    newfp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_02.txt')
    os.rename(fp, newfp)
    o.append(f'   文件名 → DOT_Strategicregions_02.txt')
    # weatherpositions 的 46 → 2
    wpfp = os.path.join(root, 'map', 'weatherpositions.txt')
    wt = io.open(wpfp, 'rb').read().decode('utf-8-sig')
    wt2 = wt.replace('46;', '2;')
    io.open(wpfp, 'wb').write(wt2.encode('utf-8'))
    o.append(f'   weatherpositions: {io.open(wpfp, "rb").read().decode("utf-8-sig").splitlines()}')

o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    o.append(f'{label} 战略区目录: {sorted(os.listdir(os.path.join(root, "map", "strategicregions")))}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

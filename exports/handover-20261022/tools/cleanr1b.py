import os, io, shutil

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
WPBAK = os.path.join(REPO, '.backups', 'weatherpos_20261015')
OUT = os.path.join(REPO, 'tools', 'cleanr1b_out.txt')
o = []

# 1) 处理残留 .crcrlf_bak（保留为证据）
for label, root in [('repo', G), ('depl', DEPL)]:
    bak = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt.crcrlf_bak')
    if os.path.exists(bak):
        dst = os.path.join(REPO, '.backups', f'r1_crcrlf_{label}.txt')
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(bak, dst)
        o.append(f'{label} 坏行尾版已存档 → {dst}')

# 2) 还原 weatherpositions 为原始 2 行版
for label, root in [('repo', G), ('depl', DEPL)]:
    src = os.path.join(WPBAK, f'{label}_weatherpositions.txt')
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(root, 'map', 'weatherpositions.txt'))
        o.append(f'{label} weatherpositions = {io.open(src, "rb").read()!r}')

# 3) 现状验证
o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt')
    raw = io.open(fp, 'rb').read()
    o.append(f'{label} r1: {len(raw)}B, CRCRLF={raw.count(bytes([13,13,10]))}(应0), CRLF={raw.count(bytes([13,10]))}')
    o.append(f'   战略区目录: {sorted(os.listdir(os.path.join(root, "map", "strategicregions")))}')
    wp = io.open(os.path.join(root, 'map', 'weatherpositions.txt'), 'rb').read()
    o.append(f'   weatherpositions: {wp!r}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

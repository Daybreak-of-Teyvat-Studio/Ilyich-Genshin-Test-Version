import os, io, re, shutil

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BD = os.path.join(REPO, '.backups', 'regtest_20261015_110919')
OUT = os.path.join(REPO, 'tools', 'wpfix_out.txt')
o = []

# 1) 恢复区域46 与区域1（用 regtest 备份 = 最新版：区域46 带 weather+naval_terrain；区域1 = 8013 省）
for label, root in [('仓库', G), ('副本', DEPL)]:
    for f, s in [('DOT_Strategicregions_01.txt', os.path.join(BD, f'repo_DOT_Strategicregions_01.txt')),
                 ('DOT_Strategicregions_46.txt', os.path.join(BD, f'repo_DOT_Strategicregions_46.txt'))]:
        shutil.copy2(s, os.path.join(root, 'map', 'strategicregions', f))
    sd = os.path.join(root, 'map', 'strategicregions')
    o.append(f'{label}: 战略区文件 = {sorted(os.listdir(sd))}')
    for f in ('DOT_Strategicregions_01.txt', 'DOT_Strategicregions_46.txt'):
        t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
        m = re.search(r'provinces=\{([^}]*)\}', t, re.S)
        o.append(f'    {f}: 省数={len(m.group(1).split())}, weather={"有" if "weather" in t else "无"}')

# 2) 取区域46 两省的 positions.txt 坐标作为 weatherposition
pos = {}
t = io.open(os.path.join(G, 'map', 'positions.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)', t):
    pos[int(m.group(1))] = (m.group(2), m.group(3), m.group(4))
o.append('')
o.append('区域46 候选省的 positions 坐标:')
pick = []
for p in (4681, 3544, 4682, 4683, 4684, 860, 1531, 2282):
    if p in pos:
        o.append(f'  p{p}: {pos[p]}')
        pick.append((p, pos[p]))
# 选两个位置差别大的
lines46 = []
if pick:
    a = pick[0]
    b = pick[-1]
    for p, (x, y, z) in (a, b):
        lines46.append(f'46;{float(x):.2f};{float(y):.2f};{float(z):.2f};big')
o.append('')
o.append('拟加入的 weatherpositions 行:')
for l in lines46:
    o.append('  ' + l)

# 3) 写入 weatherpositions（双副本，备份原文件）
bdir = os.path.join(REPO, '.backups', 'weatherpos_20261015')
os.makedirs(bdir, exist_ok=True)
for label, root in [('repo', G), ('depl', DEPL)]:
    fp = os.path.join(root, 'map', 'weatherpositions.txt')
    raw = io.open(fp, 'rb').read()
    shutil.copy2(fp, os.path.join(bdir, f'{label}_weatherpositions.txt'))
    t = raw.decode('utf-8-sig')
    nl = '\r\n'
    # 去尾换行后追加
    body = t.rstrip('\r\n')
    newbody = body + nl + nl.join(lines46)
    io.open(fp, 'wb').write(b'\xef\xbb\xbf' + newbody.encode('utf-8') if raw[:3] == b'\xef\xbb\xbf' else newbody.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig')
    o.append('')
    o.append(f'{label} weatherpositions 写入后 ({len(chk)} 字符):')
    for l in chk.splitlines():
        o.append('    ' + l)

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

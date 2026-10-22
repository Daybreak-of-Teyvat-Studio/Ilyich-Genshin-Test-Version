# -*- coding: utf-8 -*-
import os, io, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'region3_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []

SEA = [5719, 6886, 6937, 7104, 7293, 7776]   # 升序
SEA_RAW = [6886, 7293, 7776, 5719, 6937, 7104]  # 用户给的顺序（用于删除）

# 备份
for label, root in [('repo', G), ('depl', DEPL)]:
    for f in ('DOT_Strategicregions_01.txt', 'DOT_Strategicregions_02.txt'):
        shutil.copy2(os.path.join(root, 'map', 'strategicregions', f), os.path.join(BD, f'{label}_{f}'))
    for f in ('weatherpositions.txt',):
        shutil.copy2(os.path.join(root, 'map', f), os.path.join(BD, f'{label}_{f}'))
    shutil.copy2(os.path.join(root, 'localisation', 'simp_chinese', 'DOT_Strategic_Region_Names_l_simp_chinese.yml'),
                 os.path.join(BD, f'{label}_RegionNames.yml'))
o.append(f'备份: {BD}')

# 1) 区域3 文件（weather 从区域2 复制成单 CRLF）
r2 = io.open(os.path.join(G, 'map', 'strategicregions', 'DOT_Strategicregions_02.txt'), 'rb').read().decode('utf-8-sig')
wi = r2.find('\tweather={')
wblock = r2[wi:]
assert wblock.endswith('\t}\r\n}\r\n'), repr(wblock[-20:])
wblock = wblock[:-len('}\r\n')]
periods = wblock.count('\t\tperiod={')
o.append(f'weather 块: {periods} 段')
assert periods == 12

body = 'strategic_region={\r\n\tid=3\r\n\tname="DOT_STRATEGICREGIONS_49"\r\n\tprovinces={\r\n'
body += ''.join(f'{p}\r\n' for p in SEA)
body += '\t}\r\n\tnaval_terrain=water_shallow_sea\r\n' + wblock + '}\r\n'
assert body.count('{') == body.count('}')
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_03.txt')
    io.open(fp, 'wb').write(body.encode('utf-8'))
    chk = io.open(fp, 'rb').read()
    t = chk.decode('utf-8-sig')
    provs = [int(x) for x in re.search(r'provinces=\{([^}]*)\}', t, re.S).group(1).split()]
    o.append(f'{label} 区域3: {len(chk)}B, CRCRLF={chk.count(bytes([13,13,10]))}, 省={provs}, 升序={provs == sorted(provs)}, weather={"有" if "weather" in t else "无"}')

# 2) 区域1 移除这 6 省
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt')
    raw = io.open(fp, 'rb').read()
    new = raw
    for p in SEA_RAW:
        new = re.sub(rb'(?m)^' + str(p).encode() + rb'\r\n', b'', new)
    io.open(fp, 'wb').write(new)
    t = new.decode('utf-8-sig')
    provs = [int(x) for x in re.search(r'provinces=\{([^}]*)\}', t, re.S).group(1).split()]
    o.append(f'{label} 区域1: {len(new)}B (原 {len(raw)}), 省={len(provs)}, 升序={provs == sorted(provs)}, 残留6省={[p for p in SEA if p in provs]}')

# 3) weatherpositions 加区域3 两条
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'weatherpositions.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig').rstrip('\r\n')
    if '3;' not in t:
        t += '\r\n3;2479.68;9.50;953.76;big\r\n3;2462.11;9.50;971.91;big'
    io.open(fp, 'wb').write(t.encode('utf-8'))
    o.append(f'{label} weatherpositions: {io.open(fp, "rb").read().decode("utf-8-sig").splitlines()}')

# 4) 区域1 改名 暗之外海
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'localisation', 'simp_chinese', 'DOT_Strategic_Region_Names_l_simp_chinese.yml')
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    t = raw.decode('utf-8-sig')
    t2, n = re.subn(r'(DOT_STRATEGICREGIONS_01:\s*")[^"]*(")', r'\g<1>暗之外海\g<2>', t)
    t2 = t2.replace('"暗之外海" #Windrise', '"暗之外海" #Dark Sea')
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t2.encode('utf-8'))
    o.append(f'{label} 区域1 改名: {n} 处')
    for l in t2.splitlines():
        if 'DOT_STRATEGICREGIONS_01:' in l or 'DOT_STRATEGICREGIONS_49:' in l:
            o.append('   ' + l.strip()[:80])

# 5) 终检：id 连号 + 双副本一致
o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    srd = os.path.join(root, 'map', 'strategicregions')
    ids = []
    for f in sorted(os.listdir(srd)):
        tt = io.open(os.path.join(srd, f), 'rb').read().decode('utf-8-sig')
        ids.append(int(re.search(r'\bid\s*=\s*(\d+)', tt).group(1)))
    ids.sort()
    o.append(f'{label} 战略区 id: {ids} 连号={ids == list(range(1, len(ids) + 1))} 文件={sorted(os.listdir(srd))}')
a = io.open(os.path.join(G, 'map', 'strategicregions', 'DOT_Strategicregions_03.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'map', 'strategicregions', 'DOT_Strategicregions_03.txt'), 'rb').read()
o.append(f'区域3 双副本一致: {a == b}')
io.open(os.path.join(REPO, 'tools', 'region3_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

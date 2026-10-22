# -*- coding: utf-8 -*-
import os, io, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK62 = os.path.join(REPO, '.backups', 'mega014_20261014_220448', '仓库_62-State_62.txt')
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'fracfix_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []

# 备份
for label, root in [('repo', G), ('depl', DEPL)]:
    shutil.copy2(os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt'), os.path.join(BD, f'{label}_r1.txt'))
    shutil.copy2(os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_03.txt'), os.path.join(BD, f'{label}_r3.txt'))
    shutil.copy2(os.path.join(root, 'history', 'states', '62-State_62.txt'), os.path.join(BD, f'{label}_62.txt'))
o.append(f'备份: {BD}')

# 1) 4679 → 区域3；从区域1 移除
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp3 = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_03.txt')
    t = io.open(fp3, 'rb').read().decode('utf-8-sig')
    m = re.search(r'(provinces=\{)([^}]*)(\})', t, re.S)
    provs = sorted(set(int(x) for x in m.group(2).split()) | {4679})
    newt = t[:m.start()] + 'provinces={' + ''.join(f'\r\n{p}' for p in provs) + '\r\n\t}' + t[m.end():]
    io.open(fp3, 'wb').write(newt.encode('utf-8'))
    o.append(f'{label} 区域3 省={provs}')
    fp1 = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt')
    raw = io.open(fp1, 'rb').read()
    new1 = re.sub(rb'(?m)^4679\r\n', b'', raw)
    io.open(fp1, 'wb').write(new1)
    t1 = new1.decode('utf-8-sig')
    p1 = [int(x) for x in re.search(r'provinces=\{([^}]*)\}', t1, re.S).group(1).split()]
    o.append(f'{label} 区域1 省数={len(p1)}, 含4679={"4679" in t1.split("provinces={")[1].split("}")[0].split()}, 升序={p1 == sorted(p1)}')

# 2) 州62 的 state 级建筑：读合并前备份的 62 值
b = io.open(BK62, 'rb').read().decode('utf-8-sig')
o.append('')
o.append('合并前 62 州（备份）建筑块:')
mb = re.search(r'buildings\s*=\s*\{([^}]*)\}', b, re.S)
o.append('  ' + mb.group(1).strip().replace('\t', ' ')[:200])
bvals = {}
for k in ('infrastructure', 'arms_factory', 'industrial_complex', 'dockyard', 'air_base'):
    mm = re.search(k + r'\s*=\s*(\d+)', mb.group(1))
    if mm:
        bvals[k] = int(mm.group(1))
o.append(f'  备份值: {bvals}')

for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'history', 'states', '62-State_62.txt')
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    t = raw.decode('utf-8-sig')
    for k, v in bvals.items():
        t = re.sub(r'(?m)(\t\t\t' + k + r'\s*=\s*)\d+', r'\g<1>' + str(v), t, count=1)
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + t.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig')
    mb2 = re.search(r'buildings\s*=\s*\{([^}]*)\}', chk, re.S)
    o.append(f'{label} 62 州建筑块改后: ' + ' '.join(x.strip() for x in mb2.group(1).splitlines() if x.strip() and '=' in x and '{' not in x)[:160])

# 双副本一致性
for rel in ('map/strategicregions/DOT_Strategicregions_01.txt', 'map/strategicregions/DOT_Strategicregions_03.txt', 'history/states/62-State_62.txt'):
    a = io.open(os.path.join(G, rel.replace('/', os.sep)), 'rb').read()
    b2 = io.open(os.path.join(DEPL, rel.replace('/', os.sep)), 'rb').read()
    o.append(f'{rel}: 双副本一致={a == b2}')
io.open(os.path.join(REPO, 'tools', 'fracfix_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

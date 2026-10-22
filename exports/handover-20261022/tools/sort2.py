import os, io, re

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
OUT = os.path.join(REPO, 'tools', 'sort2_out.txt')
o = []
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_46.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig')
    m = re.search(r'(provinces=\{)([^}]*)(\})', t, re.S)
    provs = sorted(int(x) for x in m.group(2).split())
    new = t[:m.start()] + 'provinces={' + ''.join(f'\r\n{p}' for p in provs) + '\r\n\t}' + t[m.end():]
    io.open(fp, 'wb').write(new.encode('utf-8'))
    chk = io.open(fp, 'rb').read()
    o.append(f'{label}: {len(chk)}B CRCRLF={chk.count(bytes([13,13,10]))} 省={provs}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

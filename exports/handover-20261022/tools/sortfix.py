import os, io, shutil, datetime

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
OUT = os.path.join(REPO, 'tools', 'sortfix_out.txt')
o = []

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bd = os.path.join(REPO, '.backups', f'sort46_{stamp}')
os.makedirs(bd, exist_ok=True)

rel = os.path.join('map', 'strategicregions', 'DOT_Strategicregions_46.txt')
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, rel)
    shutil.copy2(fp, os.path.join(bd, f'{label}_46.txt'))
    raw = io.open(fp, 'rb').read()
    t = raw.decode('utf-8-sig')
    old_lines = t.splitlines()
    # 重建：头部(id/name) + provinces（升序，一行一个，无缩进，与区域1风格一致） + 其它块
    sorted_provs = sorted([4681, 3544, 4682, 4683, 4684, 860, 1531, 2282])
    # 保留原文件除 provinces 块以外的内容
    import re
    m = re.search(r'(provinces=\{)([^}]*)(\})', t, re.S)
    new_prov_block = 'provinces={' + ''.join(f'\r\n{p}' for p in sorted_provs) + '\r\n\t}'
    new_t = t[:m.start()] + new_prov_block + t[m.end():]
    # 保持无 BOM + CRLF
    io.open(fp, 'wb').write(new_t.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig')
    o.append(f'{label} 新区域46 全文:')
    for l in chk.splitlines():
        o.append('  ' + l)
    provs = [int(x) for x in re.search(r'provinces=\{([^}]*)\}', chk, re.S).group(1).split()]
    o.append(f'  → 省数={len(provs)}, 升序={provs == sorted(provs)}, 序列={provs}')
    o.append('')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

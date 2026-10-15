import os, io, re, shutil

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK = os.path.join(REPO, '.backups', 'mega014_20261014_220448')
WPBAK = os.path.join(REPO, '.backups', 'weatherpos_20261015')
OUT = os.path.join(REPO, 'tools', 'cleanr1_out.txt')
o = []

# 1) 用备份的干净区域1（单 CRLF, 8021 省）重建 8013 版：按字节删除 8 个省号行
old = io.open(os.path.join(BK, '仓库_r1_DOT_Strategicregions_01.txt'), 'rb').read()
o.append(f'备份 r1: {len(old)}B, CRCRLF={old.count(bytes([13,13,10]))}, CRLF={old.count(bytes([13,10]))}')
drop = [860, 1531, 2282, 3544, 4681, 4682, 4683, 4684]
new = old
for d in drop:
    pat = re.compile(rb'^' + str(d).encode() + rb'\r\n', re.M)
    n = len(pat.findall(new))
    new = pat.sub(b'', new)
    o.append(f'  删除省 {d}: 命中 {n} 行')
o.append(f'新 r1: {len(new)}B, CRCRLF={new.count(bytes([13,13,10]))}, CRLF={new.count(bytes([13,10]))}')
t = new.decode('utf-8-sig')
m = re.search(r'provinces=\{([^}]*)\}', t, re.S)
provs = [int(x) for x in m.group(1).split()]
o.append(f'  provinces: {len(provs)} 个, 升序={provs == sorted(provs)}, 含被删省={[p for p in drop if p in provs]}')
o.append(f'  花括号: {{={t.count(chr(123))} }}={t.count(chr(125))}')

for root in (G, DEPL):
    fp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt')
    shutil.copy2(fp, fp + '.crcrlf_bak')
    io.open(fp, 'wb').write(new)
    chk = io.open(fp, 'rb').read()
    o.append(f'  写入 {root}: {len(chk)}B, CRCRLF={chk.count(bytes([13,13,10]))} (应为 0)')
    # 删掉 .crcrlf_bak？留着当证据
    os.rename(fp + '.crcrlf_bak', os.path.join(REPO, '.backups', 'r1_crcrlf_' + os.path.basename(root) + '.txt'))

# 2) weatherpositions 还原为原始 2 行版（排除干扰）
for label, root in [('repo', G), ('depl', DEPL)]:
    src = os.path.join(WPBAK, f'{label}_weatherpositions.txt')
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(root, 'map', 'weatherpositions.txt'))
        o.append(f'  {label} weatherpositions 已还原: {io.open(src, "rb").read()!r}')

o.append('')
o.append('当前状态: 区域1=8013(干净CRLF) + 无区域46 + weatherpositions=原始2行')
for root in (G, DEPL):
    o.append(f'  {os.path.basename(root)} 战略区目录: {sorted(os.listdir(os.path.join(root, "map", "strategicregions")))}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

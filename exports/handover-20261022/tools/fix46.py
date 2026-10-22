import os, io, re, datetime, shutil

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BACKUP = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\fix46_out.txt'
o = []

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bdir = os.path.join(BACKUP, f'region46_{stamp}')
os.makedirs(bdir, exist_ok=True)

rel = os.path.join('map', 'strategicregions', 'DOT_Strategicregions_46.txt')
for label, root in [('repo', REPO), ('depl', DEPL)]:
    src = os.path.join(root, rel)
    dst = os.path.join(bdir, f'{label}_DOT_Strategicregions_46.txt')
    shutil.copy2(src, dst)
o.append(f'备份: {bdir}')

# 读 Gamma R1 的 weather 块，转 \r\r\n -> \r\n
r1 = io.open(os.path.join(REPO, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt'), 'rb').read()
i = r1.find(b'\tweather={')
assert i > 0
wblock = r1[i:]
assert wblock.endswith(b'\t}\r\r\n}\r\r\n'), repr(wblock[-20:])
wblock = wblock[:-len(b'}\r\r\n')]          # 去掉最外层 region 的收尾，保留 weather 的 \t}\r\r\n
wblock = wblock.replace(b'\r\r\n', b'\r\n') # 行尾规范化
periods = wblock.count(b'\t\tperiod={')
bets = wblock.count(b'between={')
o.append(f'weather 块: {len(wblock)}B, period×{periods}, between×{bets}')
assert periods == 12 and bets == 12

# 读当前 46，保留头部到 provinces 闭合
cur = io.open(os.path.join(REPO, rel), 'rb').read()
head_end = cur.find(b'\t}\r\n') + len(b'\t}\r\n')   # provinces 收尾
head = cur[:head_end]
tail_old = cur[head_end:]
o.append(f'原 46: head={len(head)}B, 尾部残留={tail_old!r}')
assert tail_old == b'}\r\n', '原文件结构与预期不符'

new = head + b'\tnaval_terrain=water_shallow_sea\r\n' + wblock + b'}\r\n'

# 校验：括号配对 + 省份不变
assert new.count(b'{') == new.count(b'}'), (new.count(b'{'), new.count(b'}'))
m = re.search(rb'provinces=\{\r\n(.*?)\t\}', new, re.S)
provs = m.group(1).split()
o.append(f'新文件省份: {[p.decode() for p in provs]}')
assert [p.decode() for p in provs] == ['4681', '3544', '4682', '4683', '4684', '860', '1531', '2282']
o.append(f'新 46: {len(new)}B')

# 双副本写入
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, rel)
    io.open(fp, 'wb').write(new)
    back = io.open(fp, 'rb').read()
    assert back == new
    o.append(f'{label} 写入 ✓ {len(back)}B')

# 双副本一致 + 复读验
a = io.open(os.path.join(REPO, rel), 'rb').read()
b = io.open(os.path.join(DEPL, rel), 'rb').read()
o.append(f'双副本字节一致: {a == b}')
o.append('')
o.append('---- 新文件前 8 行 ----')
for l in a.split(b'\r\n')[:8]:
    o.append(f'  {l!r}')
o.append('---- 新文件后 6 行 ----')
for l in a.split(b'\r\n')[-6:]:
    o.append(f'  {l!r}')
o.append('---- 第 13-20 行（衔接处） ----')
for l in a.split(b'\r\n')[12:20]:
    o.append(f'  {l!r}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('DONE')

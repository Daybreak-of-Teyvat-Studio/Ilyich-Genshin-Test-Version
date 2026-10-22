import os, io

LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
VANILLA = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\xc46_out.txt'
o = []

ep = os.path.join(LOGS, 'error.log')
le = io.open(ep, 'rb').read().decode('utf-8-sig', errors='replace').splitlines()

o.append('===== error.log L905-L940（温度警告上下文） =====')
for i in range(904, min(940, len(le))):
    o.append(f'L{i+1}: {le[i].rstrip()[:230]}')
o.append('')
o.append('===== error.log L1400-L1430（X crossing 上下文） =====')
for i in range(1399, min(1430, len(le))):
    o.append(f'L{i+1}: {le[i].rstrip()[:230]}')
o.append('')

# 战略区目录
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    sd = os.path.join(root, 'map', 'strategicregions')
    o.append(f'===== {label} map/strategicregions/ =====')
    if os.path.isdir(sd):
        for f in sorted(os.listdir(sd)):
            fp = os.path.join(sd, f)
            o.append(f'  {f}  {os.path.getsize(fp)}B')
    else:
        o.append('  (不存在)')
o.append('')

# 区域1 文件头 + 区域46 全文
sd = os.path.join(DEPL, 'map', 'strategicregions')
for fname in sorted(os.listdir(sd)):
    fp = os.path.join(sd, fname)
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    lines = t.splitlines()
    o.append(f'===== {fname}: {len(lines)} 行, 前 25 行 =====')
    for i, l in enumerate(lines[:25]):
        o.append(f'  {i+1}: {l!r}')
    if len(lines) > 60:
        o.append(f'  ... （中间省略） ...')
        o.append(f'  尾部 15 行:')
        for i, l in enumerate(lines[-15:], len(lines) - 14):
            o.append(f'  {i}: {l!r}')
o.append('')

# 原版战略区样例
vsd = os.path.join(VANILLA, 'map', 'strategicregions')
o.append('===== 原版 map/strategicregions/ =====')
if os.path.isdir(vsd):
    for f in sorted(os.listdir(vsd))[:8]:
        fp = os.path.join(vsd, f)
        o.append(f'  {f}  {os.path.getsize(fp)}B')
    # 读第一个文件的头部
    first = sorted(os.listdir(vsd))[0]
    t = io.open(os.path.join(vsd, first), 'rb').read().decode('utf-8-sig', errors='replace')
    lines = t.splitlines()
    o.append(f'----- 原版 {first}: {len(lines)} 行, 前 30 行 -----')
    for i, l in enumerate(lines[:30]):
        o.append(f'  {i+1}: {l!r}')
else:
    o.append('  (不存在)')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok', len(o))

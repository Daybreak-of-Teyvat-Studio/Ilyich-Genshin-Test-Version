import os, io, re

OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\crash1015_b_out.txt'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
o = []

# 1) system.log 关键行（阶段标记）
sp = os.path.join(LOGS, 'system.log')
t = io.open(sp, 'rb').read().decode('utf-8-sig', errors='replace')
lines = t.splitlines()
o.append(f'===== system.log: {len(lines)} 行 =====')
for i, line in enumerate(lines, 1):
    l = line.strip()
    if re.search(r'(?i)(load|map|state|province|strategic|database|delete|init|enter|game)', l) and len(l) < 250:
        o.append(f'L{i}: {l[:230]}')
o.append('')
o.append('--- system.log 尾部 40 行 ---')
for i, line in enumerate(lines[-40:], len(lines) - 39):
    o.append(f'L{i}: {line.rstrip()[:230]}')
o.append('')

# 2) system_debug.log 尾部
dp = os.path.join(LOGS, 'system_debug.log')
if os.path.exists(dp):
    td = io.open(dp, 'rb').read().decode('utf-8-sig', errors='replace')
    ld = td.splitlines()
    o.append(f'===== system_debug.log: {len(ld)} 行, 尾部 60 行 =====')
    for i, line in enumerate(ld[-60:], len(ld) - 59):
        o.append(f'L{i}: {line.rstrip()[:230]}')
o.append('')

# 3) error.log 里搜 map/state/strategic/building/province 关键词（非 MAP_ERROR 类）
ep = os.path.join(LOGS, 'error.log')
te = io.open(ep, 'rb').read().decode('utf-8-sig', errors='replace')
le = te.splitlines()
o.append('===== error.log 关键词行（map/state/strategic/building/province/history） =====')
n = 0
for i, line in enumerate(le, 1):
    l = line.strip()
    if re.search(r'(?i)(strategic|buildings?\.txt|history/states|state\.cpp|province|IsMapInGoodState|map\.cpp|map_loading)', l):
        n += 1
        if n <= 120:
            o.append(f'L{i}: {l[:230]}')
o.append(f'（此类共 {n} 行）')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok', len(o))

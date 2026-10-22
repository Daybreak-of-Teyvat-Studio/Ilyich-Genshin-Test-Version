import os, io, re, collections

LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
CRASH = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\crashes\hoi4_20261015_102243')
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\crash1015_out.txt'

o = []
# 1. game.log 全文
gp = os.path.join(LOGS, 'game.log')
t = io.open(gp, 'rb').read().decode('utf-8-sig', errors='replace')
o.append('===== game.log (全文, %d bytes) =====' % len(t))
o.append(t)
o.append('')

# 2. crash 目录内容
o.append('===== crash 目录 =====')
try:
    for f in os.listdir(CRASH):
        fp = os.path.join(CRASH, f)
        o.append(f'{f}  {os.path.getsize(fp)} bytes')
except Exception as e:
    o.append(str(e))
o.append('')

# 3. error.log 分类统计
ep = os.path.join(LOGS, 'error.log')
raw = io.open(ep, 'rb').read()
t = raw.decode('utf-8-sig', errors='replace')
lines = t.splitlines()
o.append(f'===== error.log: {len(lines)} 行, {len(raw)} bytes =====')

cats = collections.Counter()
samples = {}
for i, line in enumerate(lines, 1):
    l = line.strip()
    if not l:
        continue
    # 分类键
    if 'MAP_ERROR' in l:
        m = re.match(r'.*MAP_ERROR:\s*(.*)', l)
        key = 'MAP_ERROR: ' + (m.group(1)[:60] if m else l[:60])
    elif 'BUILDING IGNORED' in l:
        key = 'BUILDING IGNORED'
    elif 'not within specified state' in l:
        key = 'not within specified state'
    elif 'not over the land' in l:
        key = 'not over the land'
    elif 'invalid arguments' in l:
        key = 'invalid arguments'
    elif 'no entity' in l.lower() or "doesn't have an entity" in l:
        key = 'no entity'
    elif 'error' in l.lower() or 'unknown' in l.lower() or 'Unexpected' in l or 'invalid' in l.lower():
        key = 'OTHER-ERR: ' + re.sub(r'\d+', 'N', l)[:70]
    else:
        key = 'other'
    cats[key] += 1
    if key not in samples:
        samples[key] = (i, line.strip()[:200])

o.append('--- 分类统计（行数 Top 40）---')
for key, n in cats.most_common(40):
    ln, s = samples[key]
    o.append(f'[{n:5d}] L{ln}: {s[:180]}')
o.append('')

# 4. 所有 MAP_ERROR 全列（行号+原文）
o.append('--- 全部 MAP_ERROR 行 ---')
n = 0
for i, line in enumerate(lines, 1):
    if 'MAP_ERROR' in line:
        n += 1
        o.append(f'L{i}: {line.strip()[:220]}')
o.append(f'（共 {n} 条 MAP_ERROR）')
o.append('')

# 5. error.log 尾部 150 行
o.append('--- error.log 尾部 150 行 ---')
for i, line in enumerate(lines[-150:], len(lines) - 149):
    o.append(f'L{i}: {line.rstrip()[:220]}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('written', OUT, len(o), 'lines')

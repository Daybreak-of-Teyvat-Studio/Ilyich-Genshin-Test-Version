import os, io, re

LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\setup1015_out.txt'
o = []

sp = os.path.join(LOGS, 'setup.log')
t = io.open(sp, 'rb').read().decode('utf-8-sig', errors='replace')
lines = t.splitlines()
o.append(f'===== setup.log: {len(lines)} 行, 尾部 60 行 =====')
for i, l in enumerate(lines[-60:], len(lines) - 59):
    o.append(f'L{i}: {l.rstrip()[:230]}')
o.append('')

# error.log 尾部 30 行（确认最后写的东西）
ep = os.path.join(LOGS, 'error.log')
le = io.open(ep, 'rb').read().decode('utf-8-sig', errors='replace').splitlines()
o.append('===== error.log 真尾部 30 行 =====')
for i, l in enumerate(le[-30:], len(le) - 29):
    o.append(f'L{i}: {l.rstrip()[:230]}')
o.append('')

# 定向排查：我改过的对象是否在日志里有报错
o.append('===== 定向关键词（wonder/KQP/transfer/86/回声/分道/63/65/66/67/94/89/90/46/马斯克） =====')
pat = re.compile(r'(?i)(wonder|KQP|transfer_state|DOT_STATE_|回声|分道誓约|马斯克|strategicregion|Auto_Region)')
n = 0
for i, l in enumerate(le, 1):
    if pat.search(l):
        n += 1
        if n <= 80:
            o.append(f'L{i}: {l.strip()[:220]}')
o.append(f'（共 {n} 行命中）')
o.append('')

# text.log 尾部（本地化加载阶段最后写到哪）
tp = os.path.join(LOGS, 'text.log')
if os.path.exists(tp):
    tt = io.open(tp, 'rb').read().decode('utf-8', errors='replace')
    tl = tt.splitlines()
    o.append(f'===== text.log: {len(tl)} 行, 尾部 15 行 =====')
    for l in tl[-15:]:
        o.append(f'  {l.rstrip()[:220]}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok', len(o))

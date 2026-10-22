import os, io, datetime

LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\vanilla_log_out.txt'
o = []
for f in ('game.log', 'error.log', 'system.log'):
    fp = os.path.join(LOGS, f)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    lines = t.splitlines()
    o.append(f'===== {f}  mtime={mt:%H:%M:%S}  {len(lines)} 行 =====')
    if f == 'game.log':
        for l in lines[:40]:
            o.append('  ' + l[:200])
    else:
        o.append('  首行: ' + (lines[0][:150] if lines else '(空)'))
        o.append('  末 15 行:')
        for l in lines[-15:]:
            o.append('  ' + l[:200])
    o.append('')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

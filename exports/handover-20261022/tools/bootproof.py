import os, io, datetime

LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\bootproof_out.txt'
o = []
for f in ('game.log', 'error.log'):
    fp = os.path.join(LOGS, f)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    lines = t.splitlines()
    o.append(f'===== {f} (mtime {mt:%H:%M:%S}, {len(lines)} 行) =====')
    if f == 'game.log':
        for l in lines:
            o.append('  ' + l[:180])
    else:
        hits = [l for l in lines if any(k in l for k in ('Loaded', 'MAP_ERROR', 'Executing History', 'frontend', 'gamesetup', 'Resetting'))]
        o.append(f'  关键行 {len(hits)} 条:')
        for l in hits[:15]:
            o.append('  ' + l[:190])
        o.append('  末 3 行:')
        for l in lines[-3:]:
            o.append('  ' + l[:190])
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

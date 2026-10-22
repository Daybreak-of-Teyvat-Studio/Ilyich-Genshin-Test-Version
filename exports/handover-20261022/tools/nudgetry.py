# -*- coding: utf-8 -*-
import os, io, datetime, re, sys
sys.stdout.reconfigure(encoding='utf-8')
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\nudgetry_out.txt'
o = []
for f in ('error.log', 'system.log', 'game.log'):
    fp = os.path.join(LOGS, f)
    if not os.path.exists(fp):
        continue
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    lines = t.splitlines()
    o.append(f'===== {f}  mtime={mt:%H:%M:%S}  {len(lines)} 行 =====')
    if f == 'error.log':
        pats = ['MAP_ERROR', 'not within', 'BUILDING IGNORED', 'no air base', 'no rocket', 'no gun',
                'no port', 'coastal', 'X crossing', 'nudge', 'editor', 'invalid', 'Error']
        seen = {}
        for i, l in enumerate(lines, 1):
            for p in pats:
                if p.lower() in l.lower():
                    seen.setdefault(p, []).append((i, l.strip()[:190]))
        for p in pats:
            if p in seen:
                o.append(f'--- 命中 "{p}": {len(seen[p])} 条 ---')
                for i, l in seen[p][:12]:
                    o.append(f'  L{i}: {l}')
        o.append('--- 末 20 行 ---')
        for l in lines[-20:]:
            o.append('  ' + l[:190])
    else:
        o.append('  首行: ' + (lines[0][:140] if lines else ''))
        o.append('  末 8 行:')
        for l in lines[-8:]:
            o.append('  ' + l[:190])
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o[:60]))
print('...')
print('写入', OUT)

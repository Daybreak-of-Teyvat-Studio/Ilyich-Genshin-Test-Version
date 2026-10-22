# -*- coding: utf-8 -*-
import io, os, sys
sys.stdout.reconfigure(encoding='utf-8')
p = os.path.expanduser(r'~/Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log')
t = io.open(p, 'rb').read().decode('utf-8-sig', errors='replace')
lines = t.splitlines()
import datetime
mt = datetime.datetime.fromtimestamp(os.path.getmtime(p))
print(f'error.log mtime={mt:%H:%M:%S}, {len(lines)} 行')
for k in ('Could not find sprite type', 'Could not find "', 'MAP_ERROR', 'not within specified state',
          'coastal but has no port', 'fractioned', 'invalid state', 'State Error'):
    print(f'  [{len([l for l in lines if k in l])}] {k}')
print('--- sprite/window 报错明细 ---')
for l in lines:
    if 'Could not find sprite type' in l or 'Could not find "' in l:
        print('  ' + l.strip()[:170])

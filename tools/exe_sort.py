# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
exe = r'F:\Steam\steamapps\common\Hearts of Iron IV\hoi4.exe'
raw = open(exe, 'rb').read()
pats = [b'interesting_countr', b'interesting', b'country_entry', b'bookmark', b'country_list', b'gamesetup', b'potential_dlc']
for p in pats:
    idxs = [m.start() for m in re.finditer(re.escape(p), raw, re.I)][:8]
    print(f'--- {p!r}: {len(idxs)} ---')
    for i in idxs[:6]:
        seg = raw[max(0, i - 80):i + 120]
        vis = re.findall(rb'[\x20-\x7e]{5,}', seg)
        print('   ', b' | '.join(vis)[:220])

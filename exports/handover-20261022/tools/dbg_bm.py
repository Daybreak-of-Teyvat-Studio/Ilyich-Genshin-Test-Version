# -*- coding: utf-8 -*-
import io, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
fp = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\common\bookmarks\3_The_Traveler.txt'
t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
print('行尾 CRLF?', '\r\n' in t)
for tag in ('MOT', 'LYY', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE'):
    m = re.search(r'(?m)^[ \t]*"?' + tag + r'"?\s*=\s*\{', t)
    if not m:
        print(tag, '未匹配'); continue
    bs = t.index('{', m.start())
    d = 0; k = bs
    while k < len(t):
        if t[k] == '{': d += 1
        elif t[k] == '}':
            d -= 1
            if d == 0: break
        k += 1
    blk = t[bs:k+1]
    has_v = bool(re.search(r'(?m)^\s*version\s*=', blk))
    has_ideo = bool(re.search(r'(?m)^\s*ideology\s*=', blk))
    print(f'{tag}: 块长 {len(blk)}, 有version={has_v}, 有ideology={has_ideo} | ' + ' '.join(blk[:120].split()))

# -*- coding: utf-8 -*-
import io, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
t = io.open(os.path.join(V, 'common', 'bookmarks', 'blitzkrieg.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
print('===== 原版 blitzkrieg.txt 前 60 行 =====')
for l in t.splitlines()[:60]:
    print('  ' + l.strip()[:150])
print()
print('===== 原版条目是否含 ideas/focuses 子块 =====')
print('  ideas:', t.count('ideas'), ' focuses:', t.count('focuses'), ' history:', t.count('history'))
# 首个 country 条目
m = re.search(r'(?m)^\s*([A-Z]{3})\s*=\s*\{', t)
if m:
    s = t.index('{', m.start()); d = 0; k = s
    while k < len(t):
        if t[k] == '{': d += 1
        elif t[k] == '}':
            d -= 1
            if d == 0: break
        k += 1
    print('  首条目:', ' '.join(t[s:k+1].split())[:400])

# -*- coding: utf-8 -*-
import io, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
for label, root in [('Gamma', G), ('原版', V)]:
    p = os.path.join(root, 'common', 'countries', 'colors.txt')
    t = io.open(p, 'rb').read().decode('utf-8-sig', errors='replace')
    print('====', label, 'colors.txt', len(t), 'B; 含 major:', bool(re.search(r'(?i)\bmajor\b', t)))
    for tag in ('MOT', 'LYY', 'FRA', 'GER'):
        m = re.search(r'(?m)^\s*' + tag + r'\s*=\s*\{', t)
        if m:
            s = t.index('{', m.start())
            d = 0
            k = s
            while k < len(t):
                if t[k] == '{': d += 1
                elif t[k] == '}':
                    d -= 1
                    if d == 0: break
                k += 1
            print(f'  {tag}: {" ".join(t[s:k+1].split())[:300]}')
        else:
            print(f'  {tag}: 无条目')

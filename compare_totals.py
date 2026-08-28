# -*- coding: utf-8 -*-
import os, re
from collections import Counter

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'

def totals(states_dir):
    res = Counter()
    man = 0
    n = 0
    for fn in os.listdir(states_dir):
        if not fn.endswith('.txt'):
            continue
        n += 1
        t = open(os.path.join(states_dir, fn), encoding='utf-8').read()
        m = re.search(r'manpower\s*=\s*(\d+)', t)
        if m:
            man += int(m.group(1))
        rb = re.search(r'resources\s*=\s*\{(.*?)\}', t, re.S)
        if rb:
            for k, v in re.findall(r'(\w+)\s*=\s*([\d.]+)', rb.group(1)):
                res[k] += float(v)
    return n, man, res

bn, bm, br = totals(os.path.join(ROOT, 'Daybreak of Teyvat Beta Version', 'history', 'states'))
gn, gm, gr = totals(os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states'))

print('BETA  states=%d  manpower=%d  resources=%s' % (bn, bm, dict(br)))
print('GAMMA states=%d  manpower=%d  resources=%s' % (gn, gm, dict(gr)))
print()
print('manpower ratio gamma/beta = %.2fx' % (gm / bm if bm else 0))
for k in sorted(set(br) | set(gr)):
    b = br.get(k, 0)
    g = gr.get(k, 0)
    print('%-12s beta=%-8.0f gamma=%-8.0f ratio=%.2fx' % (k, b, g, g / b if b else 0))

# -*- coding: utf-8 -*-
import io, sys
sys.stdout.reconfigure(encoding='utf-8')
fp = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn\references\gamma-pipeline.md'
t = io.open(fp, 'rb').read().decode('utf-8-sig')
for i, l in enumerate(t.splitlines(), 1):
    if ('VP' in l and ('同一行' in l or '覆盖' in l or '多个' in l)) or '一州多个' in l:
        print(f'L{i}: {l!r}')

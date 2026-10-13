# -*- coding: utf-8 -*-
"""live_logs.py —— 游戏仍运行中：读 game.log 全文 + error.log 尾部 + 载入后地图类行"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'

print('===== game.log 全文 =====')
print(open(os.path.join(L, 'game.log'), encoding='utf-8-sig', errors='replace').read())
print()

t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]
print(f'===== error.log: {len(lines)} 行, 首行 {lines[0][:60] if lines else ""} =====')
print()
print('===== 尾部 70 行 =====')
for l in lines[-70:]:
    print('  ', l.strip()[:235])
print()
print('===== 23:10 之后的全部行（去重归类）=====')
seq = collections.OrderedDict()
n = 0
for l in lines:
    m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l)
    if m and m.group(1) >= '23:10:00':
        n += 1
        k = re.sub(r'\d+', '#', re.sub(r'\[\w+\.cpp:\d+\]', '[]', l.strip()))[:140]
        if k not in seq:
            seq[k] = [0, l.strip()[:230]]
        seq[k][0] += 1
print(f'  共 {n} 行 / {len(seq)} 类:')
for k, (cnt, sample) in seq.items():
    print(f'  ×{cnt:<4} {sample}')

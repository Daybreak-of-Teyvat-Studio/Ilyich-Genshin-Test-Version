# -*- coding: utf-8 -*-
"""log_window.py —— 打印 error.log 指定时间窗口的原始行（去重计数、按首现排序）"""
import re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
W1, W2 = '13:11:25', '13:12:10'
t = open(P, 'rb').read().decode('utf-8-sig', errors='replace')

def norm(l):
    l = re.sub(r'\[\w+\.cpp:\d+\]', '[]', l)
    l = re.sub(r'\d+', '#', l)
    l = re.sub(r'"[^"]*"', '"..."', l)
    return l[:160]

seq = collections.OrderedDict()
n_win = 0
for line in t.split('\n'):
    m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', line)
    if not m or not (W1 <= m.group(1) <= W2):
        continue
    n_win += 1
    k = norm(line.strip())
    if k not in seq:
        seq[k] = [0, line.strip()[:230]]
    seq[k][0] += 1

print(f'=== 窗口 {W1}-{W2} 共 {n_win} 行 / {len(seq)} 类（按首现顺序） ===\n')
for k, (n, sample) in seq.items():
    print(f'×{n:<4} {sample}')

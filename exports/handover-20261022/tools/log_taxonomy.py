# -*- coding: utf-8 -*-
"""log_taxonomy.py —— error.log 去重归类：按模式聚合，按首次出现时间排序"""
import re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
t = open(P, 'rb').read().decode('utf-8-sig', errors='replace')

# 模式归一化：去掉数字、引号内容
def norm(l):
    l = l.strip()
    l = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\[\w+\]', '', l)          # 时间戳
    l = re.sub(r'\[\w+\.cpp:\d+\]', '[FILE.cpp:N]', l)            # 文件名行号
    l = re.sub(r'\d+', '#', l)                                    # 数字
    l = re.sub(r'"[^"]*"', '"..."', l)                            # 引号内容
    l = re.sub(r'\b[A-Z]{3}\b', 'TAG', l)                         # 三字母 tag
    return l[:130]

groups = collections.OrderedDict()
for line in t.split('\n'):
    if not line.strip():
        continue
    m = re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', line)
    ts = m.group(1) if m else '??'
    k = norm(line)
    if k not in groups:
        groups[k] = [0, ts, line.strip()[:200]]
    groups[k][0] += 1

print(f'=== {len(groups)} 类错误（按首次出现时间） ===\n')
for k, (n, ts, sample) in sorted(groups.items(), key=lambda x: x[1][1]):
    print(f'[首现 {ts}] ×{n:<5} {k}')
    if n > 0:
        print(f'          例: {sample}')

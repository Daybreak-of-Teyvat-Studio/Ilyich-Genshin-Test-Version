# -*- coding: utf-8 -*-
"""was_lookup.py —— 从 644 州全表反查关键映射"""
import re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = None
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = open(os.path.join(ROOT, 'tools', 'find_was_numbers_out.txt'), encoding='utf-8', errors='replace').read()
pairs = re.findall(r'(\d+)\u2192(\d+)', t)
# 表格式 = was→now
was2now = {int(a): int(b) for a, b in pairs}
now2was = {int(b): int(a) for a, b in pairs}
print('=== 当前号 <- 原号 ===')
for cur in (62, 63, 64, 65, 66, 67, 94, 110, 706, 707, 708, 709):
    print(f'  当前 {cur} <- 原号 {now2was.get(cur, "（表里无）")}')
print()
print('=== 原号 706-709 现在在哪 ===')
for w in (706, 707, 708, 709):
    print(f'  原号 {w} -> 当前 {was2now.get(w, "（表里无）")}')
print()
print('=== 全表中原号 > 700 的（尾部段的历史）===')
big = sorted((w, n) for w, n in was2now.items() if w >= 700)
for w, n in big:
    print(f'  {w} -> {n}')

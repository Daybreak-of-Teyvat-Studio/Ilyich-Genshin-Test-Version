# -*- coding: utf-8 -*-
"""naval_check.py —— 全部 OOB 文件括号平衡 + PRI 结构逐行检查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== 所有 history/units 文件括号平衡 ===')
bad = []
for f in sorted(glob.glob(os.path.join(G, 'history', 'units', '*.txt'))):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    # 去注释与字符串后数括号（简化：直接数）
    depth = 0
    mn = 0
    for ch in t:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            mn = min(mn, depth)
    if depth != 0 or mn < 0:
        bad.append((os.path.basename(f), depth, mn))
        print(f'  ✗ {os.path.basename(f)}: 终深 {depth}，最小 {mn}')
if not bad:
    print('  全部平衡 ✓')

print()
print('=== PRI_1936_Naval.txt 60-90 行（完整行，不截断）===')
p = os.path.join(G, 'history', 'units', 'PRI_1936_Naval.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read().splitlines()
for i in range(58, min(90, len(t))):
    print(f'  {i+1}: {t[i].rstrip()[:200]}')

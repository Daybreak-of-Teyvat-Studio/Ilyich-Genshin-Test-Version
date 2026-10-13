# -*- coding: utf-8 -*-
"""country_struct.py —— 检查两个国家文件的包裹结构"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

for f in ('FAV - Favonius.txt', 'INA - Inazuma.txt'):
    p = os.path.join(G, 'history', 'countries', f)
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print('=' * 62)
    print(f, len(t), 'chars, 大括号 {=%d }=%d' % (t.count('{'), t.count('}')))
    print('--- 头 8 行 ---')
    for l in t.split('\n')[:8]:
        print('  ', l.rstrip()[:120])
    print('--- 尾部 14 行 ---')
    for l in t.split('\n')[-14:]:
        print('  ', l.rstrip()[:120])
    # 顶层左括号的位置与层级追踪（找所有深度 0→1 的 `X = {`）
    depth = 0
    tops = []
    for m in re.finditer(r'[{}]|\w+\s*=\s*\{', t):
        seg = m.group(0)
        if seg == '}':
            depth = max(0, depth - 1)
        elif seg == '{':
            depth += 1
        else:
            if depth == 0:
                tops.append((m.start(), seg))
            depth += 1
    print('  顶层块（深度0级）:', [(pos, name.strip()) for pos, name in tops][:6])
    # create_equipment_variant 的深度
    for m in list(re.finditer(r'create_equipment_variant\s*=\s*\{', t))[:8]:
        # 计算该位置的深度
        d = 0
        i = 0
        pos = m.start()
        while i < pos:
            if t[i] == '{':
                d += 1
            elif t[i] == '}':
                d -= 1
            i += 1
        # 该变体的名字
        nb = re.search(r'name\s*=\s*"([^"]*)"', t[pos:pos + 200])
        print(f'    variant @{pos} 深度={d} name={nb.group(1) if nb else "?"}')

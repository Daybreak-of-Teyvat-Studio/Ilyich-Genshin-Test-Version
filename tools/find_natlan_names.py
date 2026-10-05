# -*- coding: utf-8 -*-
"""find_natlan_names.py v2 —— 纳塔名字当前挂在哪个 key（只看 DOT_STATE_/VICTORY_POINTS_ key），结果写 utf-8 文件"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOC = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'localisation')
OUT = os.path.join(ROOT, 'tools', 'natlan_names_now.txt')
NAMES = ['柴薪之丘', '圣火竞技场', '烟谜主', '溶水域', '流泉之众', '悬木人', '彩石顶',
         '祖遗庙宇', '窃火者密岛', '燃素开采研究所', '浮土静界', '玉裙之丘', '花羽会']
lines = []
for p in sorted(glob.glob(os.path.join(LOC, '**', '*.yml'), recursive=True)):
    rel = os.path.relpath(p, LOC)
    if not rel.startswith('simp_chinese'):
        continue
    for i, l in enumerate(open(p, encoding='utf-8-sig', errors='replace').read().splitlines(), 1):
        m = re.match(r'^\s*((?:DOT_STATE|VICTORY_POINTS)_\d+):\d*\s+"([^"]*)"', l)
        if not m:
            continue
        for n in NAMES:
            if n in m.group(2):
                lines.append(f'{n:<10} {rel}:{i}  {m.group(1)} = "{m.group(2)}"')
open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) or '(无命中)')
print(f'{len(lines)} 条 → {OUT}')

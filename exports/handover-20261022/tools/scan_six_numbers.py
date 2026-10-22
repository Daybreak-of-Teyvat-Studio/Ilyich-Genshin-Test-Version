# -*- coding: utf-8 -*-
"""scan_six_numbers.py —— 全语法扫描六个海州号的引用（只读）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

SIX = ('740', '741', '744', '745', '747', '748')
# 排除：原版残留文件
EXCLUDE = ('resource_prospecting', '14_sea_on_actions', '12_wuw_on_actions')

pats = [
    ('state 语法', re.compile(r'((?:state|owns_state|controls_state|transfer_state)\s*=\s*)(\d+)(?!\d)')),
    ('裸作用域 N = {', re.compile(r'(?m)^(\s*)(\d+)(\s*=\s*\{)')),
    ('prioritize/列表内裸数', re.compile(r'(prioritize\s*=\s*\{[^}]*?\b(\d+)\b)', re.S)),
    ('building效果相关', re.compile(r'((?:add_building_construction|add_extra_state_shared_building_slots|set_building_level|remove_building|damage_building)[^\n]{0,120})')),
]
found = []
for sub in ('common', 'events'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if any(x in rel for x in EXCLUDE):
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            lines = t.split('\n')
            for i, l in enumerate(lines):
                for num in SIX:
                    if re.search(r'\b' + num + r'\b', l):
                        # 已有 state = 语法的（上轮已改）跳过
                        if re.search(r'(?:state|owns_state|controls_state|transfer_state)\s*=\s*' + num + r'\b', l):
                            continue
                        # 排除明显噪声：days/cost/amount/value/月数
                        if re.search(r'(?:days|cost|amount|value|manpower|num_|>|<)\s*=?\s*' + num + r'\b', l):
                            continue
                        found.append((rel, i + 1, num, l.strip()[:130]))

print(f'=== 六个号在（state 语法之外的）行 {len(found)} 处 ===')
cur = None
for rel, ln, num, ctx in found:
    if rel != cur:
        print(f'\n--- {rel} ---')
        cur = rel
    print(f'  L{ln} [{num}]: {ctx}')

# 另外：building 效果块里任何数字（跨行）—— 针对 add_extra_state_shared_building_slots 类
print()
print('=== add_extra_state_shared_building_slots / add_building_construction 上下文（含数字的）===')
for dirpath, dirnames, filenames in os.walk(os.path.join(G, 'common')):
    for fn in filenames:
        if not fn.endswith('.txt'):
            continue
        rel = os.path.relpath(os.path.join(dirpath, fn), G)
        if any(x in rel for x in EXCLUDE):
            continue
        t = open(os.path.join(dirpath, fn), encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(r'add_extra_state_shared_building_slots', t):
            ln = t[:m.start()].count('\n') + 1
            seg = t[m.start():m.start() + 120].replace('\n', ' ')
            print(f'  {rel} L{ln}: {seg[:120]}')

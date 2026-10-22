# -*- coding: utf-8 -*-
"""verify_effect_pairs.py —— 验证"owns_state 号 vs 效果号"的配对规律（读 3-4 个完整决策）"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
p = os.path.join(G, 'common', 'decisions', 'DOT_Resources.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
ls = t.split('\n')

# 找所有决策名与块范围
decs = [(i + 1, l.strip()) for i, l in enumerate(ls) if re.match(r'^\s*DOT_\w+\s*=\s*\{', l)]
print(f'共 {len(decs)} 个决策:')
for ln, name in decs:
    print(f'  L{ln}: {name[:60]}')

print()
print('=== 每个决策块内的 owns_state 号 与 裸作用域效果号 配对 ===')
for idx, (ln, name) in enumerate(decs):
    end = decs[idx + 1][0] - 1 if idx + 1 < len(decs) else len(ls)
    blk = ls[ln - 1:end]
    bt = '\n'.join(blk)
    owns = sorted(set(re.findall(r'owns_state\s*=\s*(\d+)', bt)))
    hl = sorted(set(re.findall(r'highlight_state_targets\s*=\s*\{\s*state\s*=\s*(\d+)', bt.replace('\n', ' '))))
    eff = sorted(set(re.findall(r'(?m)^\s*(\d+)\s*=\s*\{\s*(?:set_state_flag|$)', bt)))
    eff2 = sorted(set(re.findall(r'(?m)^\s*(\d+)\s*=\s*\{', bt)))
    print(f'  {name[:36]:38s} owns={owns} highlight={hl} 效果块号={eff2}')

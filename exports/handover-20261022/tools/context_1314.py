# -*- coding: utf-8 -*-
"""context_1314.py —— 看 8 行引用的上下文 + 相关 id 的 beta/gamma 位置"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')


def show(path, lines, before=6, after=6):
    t = open(os.path.join(G, path), encoding='utf-8-sig', errors='replace').read().splitlines()
    for ln in lines:
        print(f'--- {path} : {ln} ---')
        for i in range(max(0, ln - before - 1), min(len(t), ln + after)):
            mark = '>>>' if i == ln - 1 else '   '
            print(f'{mark} {i+1}: {t[i]}')
        print()


show('common/decisions/DVA_decisions.txt', [7382, 7414], before=8, after=4)
show('common/national_focus/DVA_focustree.txt', [1851, 1855, 1924], before=8, after=4)
show('common/on_actions/ANR_influence_on_actions.txt', [384], before=6, after=6)
show('history/units/DVA_1936.txt', [36], before=4, after=4)

print('=== 相关省在 beta/gamma 的位置 ===')
def loc_of(base, pid):
    hits = []
    for f in glob.glob(os.path.join(base, 'history', 'states', '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        if pm and re.search(r'\b' + str(pid) + r'\b', pm.group(1)):
            sid = re.search(r'\bid\s*=\s*(\d+)', t).group(1)
            om = re.search(r'\bowner\s*=\s*(\w+)', t)
            hits.append((sid, om.group(1) if om else '海'))
    return hits

for pid in (1314, 442, 2463, 4101, 4128, 4120, 1799, 4147, 4159, 2397, 459, 1243, 4236):
    print(f'  p{pid}: beta={loc_of(B, pid)}  gamma={loc_of(G, pid)}')

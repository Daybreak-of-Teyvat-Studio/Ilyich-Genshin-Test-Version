# -*- coding: utf-8 -*-
"""find_landmark.py —— 定位两个缺 entity 的地标建筑"""
import os, re, sys, glob, subprocess

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'

TARGETS = ['landmark_institute_of_tower', 'landmark_Lei_Line_research_center']
# 顺带查全部 landmark 类型定义
def scan_tree(base, tag, patterns):
    found = {}
    for pat in patterns:
        hits = []
        for dirpath, dirnames, filenames in os.walk(base):
            if any(x in dirpath for x in ('.git', '.backups', '.ai_gamma_map', 'node_modules')):
                continue
            for fn in filenames:
                if not fn.endswith(('.txt', '.gfx', '.asset')):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    t = open(p, encoding='utf-8-sig', errors='replace').read()
                except Exception:
                    continue
                if pat in t:
                    rel = os.path.relpath(p, base)
                    n = t.count(pat)
                    hits.append((rel, n))
        found[pat] = hits
    for pat, hits in found.items():
        print(f'  [{tag}] {pat}: {len(hits)} 个文件')
        for rel, n in hits[:15]:
            print(f'      {rel} ×{n}')
    return found

print('=' * 70)
print('【A】gamma 树内搜索')
scan_tree(G, 'gamma', TARGETS)

print()
print('=' * 70)
print('【B】beta 树内搜索')
scan_tree(B, 'beta', TARGETS)

print()
print('=' * 70)
print('【C】原版搜索')
scan_tree(V, 'vanilla', TARGETS)

# 找 gamma 中所有 landmark_* 定义（common/buildings）
print()
print('=' * 70)
print('【D】gamma common/buildings 里所有 landmark_ 定义与 entity 行')
for f in glob.glob(os.path.join(G, 'common', 'buildings', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'(?m)^(landmark_\w+)\s*=\s*\{', t):
        name = m.group(1)
        # 抓块内 entity 行
        blk_start = m.end() - 1
        depth, i = 0, blk_start
        while i < len(t):
            if t[i] == '{':
                depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blk = t[blk_start:i + 1]
        ent = re.search(r'(?m)^\s*entity\s*=\s*(\S+)', blk)
        print(f'  {os.path.basename(f)}: {name} entity={ent.group(1) if ent else "★无 entity 行"}')

# -*- coding: utf-8 -*-
"""icon_system.py —— DOT_Goal/DOT_Idea 图标系统的 sprite 名与使用者"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== ① DOT_Icons_DOT_Goal.gfx 中 740 段（L25120-25200）===')
p = os.path.join(G, 'interface', 'DOT_Icons_DOT_Goal.gfx')
ls = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
for i in range(25118, min(len(ls), 25200)):
    print(f'  L{i+1}: {ls[i].rstrip()[:130]}')

print()
print('=== ② 这两个 gfx 里 per-number sprite 的总数 ===')
t1 = open(os.path.join(G, 'interface', 'DOT_Icons_DOT_Goal.gfx'), encoding='utf-8-sig', errors='replace').read()
t2 = open(os.path.join(G, 'interface', 'DOT_Icons_DOT_Idea.gfx'), encoding='utf-8-sig', errors='replace').read()
g_names = re.findall(r'name\s*=\s*"(GFX_[^"]+)"', t1)
i_names = re.findall(r'name\s*=\s*"(GFX_[^"]+)"', t2)
print(f'  Goal sprites: {len(g_names)} 个, 例: {g_names[:5]}')
print(f'  Idea sprites: {len(i_names)} 个, 例: {i_names[:5]}')
# 带数字的
g_num = [n for n in g_names if re.search(r'\d{3}', n)]
i_num = [n for n in i_names if re.search(r'\d{3}', n)]
print(f'  Goal 带数字名: {len(g_num)} 例: {g_num[:8]}')
print(f'  Idea 带数字名: {len(i_num)} 例: {i_num[:8]}')

print()
print('=== ③ 全 mod 搜这些 sprite 名的使用者（GFX_idea_DOT_0 / GFX_goal_DOT_ + 数字 形式）===')
for pat in (r'GFX_idea_DOT_\d+', r'GFX_goal_DOT_\d+', r'GFX_goal_DOTState', r'GFX_state_goal'):
    hits = []
    for root2, dirnames, filenames in os.walk(G):
        if any(x in root2 for x in ('.backups', '.git', 'localisation')):
            continue
        for fn in filenames:
            if not fn.endswith(('.txt', '.gui', '.gfx')):
                continue
            fp = os.path.join(root2, fn)
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for m in re.finditer(pat, t):
                ln = t[:m.start()].count('\n') + 1
                hits.append((os.path.relpath(fp, G), ln, t[max(0, m.start() - 60):m.end() + 30].replace('\n', ' ')[:120]))
    print(f'  --- {pat}: {len(hits)} 处 ---')
    seen = set()
    for rel, ln, ctx in hits:
        k = rel
        if k in seen:
            continue
        seen.add(k)
        print(f'    {rel} L{ln}: ...{ctx}...')
        if len(seen) > 8:
            break

print()
print('=== ④ DOT_Idec/DOT_Goal 的 png 文件清单（数字范围）===')
for d in ('gfx/interface/ideas/DOT_Idea', 'gfx/interface/goals/DOT_Goal'):
    dd = os.path.join(G, *d.split('/'))
    if os.path.isdir(dd):
        fs = sorted(os.listdir(dd))
        nums = sorted(int(m.group(1)) for f in fs for m in [re.search(r'\((\d+)\)', f)] if m)
        print(f'  {d}: {len(fs)} 个文件, 数字 {nums[:5]}...{nums[-5:] if nums else ""} (共{len(nums)})')
    else:
        print(f'  {d}: 目录不存在')

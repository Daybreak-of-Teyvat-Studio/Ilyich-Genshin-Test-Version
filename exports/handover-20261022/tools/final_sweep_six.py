# -*- coding: utf-8 -*-
"""final_sweep_six.py —— 全树扫描六个号（排除已查目录），重点 map/ 目录"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

SIX = ('740', '741', '744', '745', '747', '748')
TOKEN = re.compile(r'(?<![\d])(740|741|744|745|747|748)(?![\d])')

# 先单独看 map/ 目录的文件结构
print('=== map/ 目录各文件头（找 state/building 键的）===')
for f in sorted(glob.glob(os.path.join(G, 'map', '*'))):
    if os.path.isdir(f):
        continue
    b = os.path.basename(f)
    if b.endswith('.bmp') or b.endswith('.csv'):
        continue
    sz = os.path.getsize(f)
    if sz == 0:
        continue
    try:
        t = open(f, encoding='utf-8-sig', errors='replace').read(400)
    except Exception:
        continue
    hdr = t.split('\n')[:3]
    print(f'  {b} ({sz:,}B): {[h.strip()[:70] for h in hdr]}')

print()
print('=== 全树（除已排查的 common/events/history/states 与 loc）六个号命中 ===')
skip_dirs = ('.backups', '.git', 'localisation', 'node_modules')
found = {}
for dirpath, dirnames, filenames in os.walk(G):
    if any(x in dirpath for x in skip_dirs):
        continue
    rel = os.path.relpath(dirpath, G)
    if rel.startswith('common') or rel.startswith('events'):
        continue
    for fn in filenames:
        if not fn.endswith(('.txt', '.csv', '.asset', '.gfx')):
            continue
        fp = os.path.join(dirpath, fn)
        if os.path.basename(fp).startswith('buildings.txt') and rel == 'map':
            continue  # 已单独查过
        try:
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
        except Exception:
            continue
        for i, l in enumerate(t.split('\n')):
            for m in TOKEN.finditer(l):
                key = os.path.relpath(fp, G)
                found.setdefault(key, []).append((i + 1, m.group(1), l.strip()[:120]))

for rel, hits in sorted(found.items()):
    print(f'\n--- {rel} ({len(hits)} 处) ---')
    for ln, num, ctx in hits[:12]:
        print(f'  L{ln} [{num}]: {ctx}')

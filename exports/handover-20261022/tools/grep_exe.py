# -*- coding: utf-8 -*-
"""grep_exe.py —— 从 hoi4.exe 挖 "Failed to load the map" 弹窗的上下文字符串"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'

# 找 exe
cands = [os.path.join(V, 'hoi4.exe')]
for f in os.listdir(V):
    if f.lower().endswith('.exe'):
        cands.append(os.path.join(V, f))
for p in cands:
    if os.path.exists(p):
        print(f'  {p}: {os.path.getsize(p):,} B')
target = os.path.join(V, 'hoi4.exe')

raw = open(target, 'rb').read()
print('扫描字符串…')
# 提取 ASCII 字符串及其偏移
strs = [(m.start(), m.group(0)) for m in re.finditer(rb'[\x20-\x7e]{5,}', raw)]
print(f'共 {len(strs)} 段字符串')

def show_context(needle, span=3000, limit=60):
    nb = needle.encode()
    hits = [i for i, (off, s) in enumerate(strs) if needle.encode() in s]
    print(f'\n=== "{needle}" 命中 {len(hits)} 段 ===')
    for i in hits[:2]:
        off = strs[i][0]
        print(f'  --- 偏移 {off:#x} 附近字符串 ---')
        n = 0
        for j, (o, s) in enumerate(strs):
            if abs(o - off) < span and o != off:
                try:
                    txt = s.decode('ascii', errors='replace')
                except Exception:
                    continue
                if len(txt) > 5 and not txt.startswith(('http', 'C:\\', 'CVS')):
                    print(f'    {o:#x}: {txt[:150]}')
                    n += 1
                    if n > limit:
                        break
        break

for kw in ('Failed to load the map', 'map defition', 'map definition'):
    show_context(kw)

# 兜底关键词
for kw in ('IsMapInGoodState', 'good state', 'Map invalid', 'MAP_ERROR'):
    n = sum(1 for _, s in strs if kw.encode() in s)
    print(f'\n"{kw}": {n} 段命中')

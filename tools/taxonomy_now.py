# -*- coding: utf-8 -*-
"""taxonomy_now.py —— 当前 23:36 日志的模块分类 + 找今天修改可能引入的新错误"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'
t = open(os.path.join(L, 'error.log'), encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]
print(f'总行数 {len(lines)}  首行 {lines[0][:60]}')

mod = collections.Counter()
mod_first = {}
for l in lines:
    m = re.search(r'\[(\w+)\.(?:cpp|h):\d+\]', l)
    if m:
        mod[m.group(1)] += 1
        mod_first.setdefault(m.group(1), re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l).group(1) if re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', l) else '?')
print('\n=== 模块行数 ===')
for k, v in mod.most_common(30):
    print(f'  {k:36s} {v:>5} (首现 {mod_first[k]})')

print()
print('=== 与我们今天改过的东西相关的新错误（loc/effects/decisions/ideology/scope）===')
PAT = re.compile(r'(?i)(invalid scope|add_resource|set_state_flag|DOT_Resources|localisation|\.yml|effect|idea|owns_state|controls_state|transfer_state|building)')
seen = collections.OrderedDict()
for l in lines:
    if PAT.search(l):
        k = re.sub(r'\d+', '#', l.strip())[:130]
        if k not in seen:
            seen[k] = l.strip()[:220]
for k, sample in list(seen.items())[:40]:
    print('  ', sample)

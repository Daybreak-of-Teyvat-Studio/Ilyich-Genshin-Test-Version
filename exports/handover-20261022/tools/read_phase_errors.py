# -*- coding: utf-8 -*-
"""read_phase_errors.py —— 失败运行中，状态/国家加载阶段（12:50:2x-5x）的所有非 GUI 错误"""
import re, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()
print(f'共 {len(ls)} 行')

print()
print('=== 是否还有 dockyard / 错州块 ===')
n = 0
for l in ls:
    if 'dockyard' in l or 'Trying to set' in l:
        n += 1
        print(' ', l[:170])
print(f'  {n} 行' if n else '  0 行（已消除 ✓）')

print()
print('=== 12:50 时段非 GUI 错误（去噪） ===')
NOISE = ('containerwindow', 'frontendgamesetupview', 'gfx_texture_loader', 'graphics.cpp',
         'pdx_audio', 'assetfactory_audio', 'eventtarget.cpp', 'triggerbase.cpp')
seen = collections.Counter()
samples = {}
for l in ls:
    if not re.match(r'\[12:5[0-9]', l):
        continue
    if any(x in l for x in NOISE):
        continue
    key = re.sub(r'\d+', '#', l.split(']')[-1][:90])
    seen[key] += 1
    samples.setdefault(key, l[:180])
for k, c in seen.most_common(40):
    print(f'  ×{c}  {samples[k]}')

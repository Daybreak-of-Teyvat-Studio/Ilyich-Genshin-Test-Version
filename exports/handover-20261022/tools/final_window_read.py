# -*- coding: utf-8 -*-
"""final_window_read.py —— 新 WER 签名 + debug 日志的死亡窗口内容"""
import os, re, sys, glob, subprocess

sys.stdout.reconfigure(encoding='utf-8')

print('=== 新 WER 记录（7c5c2994）签名 ===')
d = glob.glob(r'C:\ProgramData\Microsoft\Windows\WER\ReportArchive\AppCrash_hoi4*7c5c2994*')
if d:
    p = os.path.join(d[0], 'Report.wer')
    raw = open(p, 'rb').read()
    try:
        t = raw.decode('utf-16-le')
    except Exception:
        t = raw.decode('utf-8', errors='replace')
    for l in t.splitlines():
        if any(k in l for k in ('EventTime', 'Sig[6]', 'Sig[7]', 'Sig[8]', 'Sig[3]')):
            print(' ', l[:120])
    import datetime
    print('  目录时间:', datetime.datetime.fromtimestamp(os.path.getmtime(d[0])))
else:
    print('  未找到')

print()
print('=== debug 日志死亡窗口 13:11:40-13:12:10（去噪）===')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()
NOISE = ('containerwindow', 'frontendgamesetupview', 'gfx_texture_loader', 'graphics.cpp')
n = 0
for l in ls:
    m = re.match(r'\[13:11:(4[0-9]|5[0-9])\]', l)
    if m and not any(x in l for x in NOISE):
        n += 1
        if n <= 50:
            print(' ', l[:180])
print(f'  （窗口内非 GUI 行数: {n}）')

print()
print('=== 全日志中 闲云机 / equipment variant 相关（确认修复生效）===')
cnt = 0
for l in ls:
    if '闲云机' in l or 'Unbuildable' in l:
        cnt += 1
        if cnt <= 8:
            print(' ', l[:180])
print(f'  共 {cnt} 行')

print()
print('=== 25% 之后到进游戏之间的其他错误分类（13:11:43 起）===')
import collections
c = collections.Counter()
samples = {}
for l in ls:
    if re.match(r'\[13:1[12]:', l) and not any(x in l for x in ('containerwindow', 'frontend', 'gfx_', 'graphics', 'pdx_audio', 'assetfactory', 'eventtarget.cpp', 'triggerbase')):
        key = re.sub(r'\d+', '#', l.split(']')[-1][:70])
        c[key] += 1
        samples.setdefault(key, l[:170])
for k, v in c.most_common(20):
    print(f'  ×{v}  {samples[k]}')

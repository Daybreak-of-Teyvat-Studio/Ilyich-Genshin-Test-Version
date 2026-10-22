# -*- coding: utf-8 -*-
"""check_now2.py —— 当前 error.log 是否还有 :1657 / :679 / MAP_ERROR，及最新时间戳"""
import os, re, sys, time

sys.stdout.reconfigure(encoding='utf-8')
L = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs'
p = os.path.join(L, 'error.log')
print('error.log mtime:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p))))
t = open(p, encoding='utf-8-sig', errors='replace').read()
lines = [l for l in t.split('\n') if l.strip()]
print('总行数:', len(lines))
print('首行:', lines[0][:100] if lines else '')
print('末行:', lines[-1][:160] if lines else '')

for name, pat in ((':1657 地标', r'mapbuildings\.cpp:1657'),
                  (':679 not-over-land', r'mapbuildings\.cpp:679'),
                  (':716 not-within-state', r'mapbuildings\.cpp:716'),
                  (':634 invalid-args', r'mapbuildings\.cpp:634'),
                  ('strategicair MAP_ERROR', r'strategicair\.cpp:\d+\]: MAP_ERROR'),
                  ('X-crossing', r'X crossing')):
    hits = [l.strip() for l in lines if re.search(pat, l)]
    ts = [re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', h).group(1) for h in hits if re.match(r'^\[(\d{2}:\d{2}:\d{2})\]', h)]
    print(f'  {name}: {len(hits)} 条' + (f'  时间范围 {min(ts)}~{max(ts)}' if ts else ''))
    if hits:
        print('    例:', hits[0][:200])

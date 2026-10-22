# -*- coding: utf-8 -*-
"""ship_variant_diag.py —— 船变体错误全列 + MOT 相关行 + WER 检查"""
import os, re, sys, glob, subprocess

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== 当前日志中所有 equipment_effects 错误（完整）===')
P = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log'
ls = open(P, encoding='utf-8', errors='replace').read().splitlines()
for i, l in enumerate(ls, 1):
    if 'equipment_effects' in l or 'Unbuildable' in l or 'create_equipment_variant' in l:
        print(f'  {i}: {l[:230]}')

print()
print('=== MOT - Mondstadt.txt 200-240 行 ===')
p = os.path.join(G, 'history', 'countries', 'MOT - Mondstadt.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read().splitlines()
for i in range(199, min(240, len(t))):
    print(f'  {i+1}: {t[i].rstrip()[:140]}')

print()
print('=== WER 今日 hoi4 记录 ===')
cmd = ['powershell', '-NoProfile', '-Command',
       "$a=@('C:\\ProgramData\\Microsoft\\Windows\\WER\\ReportArchive','C:\\ProgramData\\Microsoft\\Windows\\WER\\ReportQueue'); "
       "Get-ChildItem $a -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '*hoi4*' -and $_.LastWriteTime -gt (Get-Date).AddHours(-24) } | "
       "ForEach-Object { Write-Host ($_.LastWriteTime.ToString('MM-dd HH:mm:ss') + '  ' + $_.Name) }"]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout or '(无)')

# -*- coding: utf-8 -*-
"""verify_suspicious.py —— 验证两个疑点
A) Ilyich_Hero_Event.txt 的 has_full_control_of 修复是否还在（仓库+副本）
B) 今早日志的 13414/48 缺失与"复制未完成启动"假说的最终确认（副本 ctime 证据）"""
import os, re, sys, datetime

sys.stdout.reconfigure(encoding='utf-8')
R = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

print('=== A. Ilyich_Hero_Event.txt 修复状态 ===')
for name, base in (('仓库', R), ('副本', D)):
    p = os.path.join(base, 'events', 'Ilyich_Hero_Event.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    bad = t.count('has_full_control_of state =')
    good = t.count('has_full_control_of =')
    print(f'  {name}: 坏写法 {bad}，好写法 {good}，mtime {datetime.datetime.fromtimestamp(os.path.getmtime(p))}')

print()
print('=== B. ctime 证据：副本文件何时被创建/重写 ===')
for rel in ('map\\definition.csv', 'map\\provinces.bmp', 'history\\states\\6-State_6.txt',
            'history\\states\\1-State_1.txt', 'common\\defines\\DOT_defines.txt' if os.path.exists(os.path.join(D, 'common', 'defines', 'DOT_defines.txt')) else 'common\\defines'):
    p = os.path.join(D, rel)
    if os.path.exists(p):
        c = datetime.datetime.fromtimestamp(os.path.getctime(p))
        m = datetime.datetime.fromtimestamp(os.path.getmtime(p))
        print(f'  {rel}: 创建 {c}，修改 {m}')

# -*- coding: utf-8 -*-
"""dump_stale_blocks.py —— 打印 9 处错州块的原始内容 + 目标州现状（决定删/搬）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')


def read(sid):
    p = glob.glob(os.path.join(ST, f'{sid}-State_*.txt'))[0]
    return open(p, encoding='utf-8-sig', errors='replace').read()


CASES = [(1772, 15, 384), (1368, 152, 150), (78, 186, 174), (1821, 186, 174),
         (2001, 204, 208), (356, 208, 204), (2733, 249, 237), (182, 415, 405), (1157, 470, 489)]

for pid, old_s, new_s in CASES:
    t_old = read(old_s)
    t_new = read(new_s)
    m_old = re.search(r'(?m)^\s*' + str(pid) + r'\s*=\s*\{[^}]*\}\s*$', t_old)
    m_new = re.search(r'(?m)^\s*' + str(pid) + r'\s*=\s*\{[^}]*\}\s*$', t_new)
    print(f'p{pid}: 旧州 s{old_s} 块 = {repr(m_old.group(0).strip() if m_old else None)}')
    print(f'        新州 s{new_s} 块 = {repr(m_new.group(0).strip() if m_new else None)}')

print()
print('=== 5 个无效船坞的原始行 ===')
for sid in (15, 54, 125, 238, 249):
    t = read(sid)
    m = re.search(r'(?m)^[ \t]*dockyard[ \t]*=[ \t]*\d+[ \t]*\r?$', t)
    print(f'  s{sid}: {repr(m.group(0) if m else None)}')

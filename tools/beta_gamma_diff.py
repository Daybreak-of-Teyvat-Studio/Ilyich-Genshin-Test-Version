# -*- coding: utf-8 -*-
"""beta_gamma_diff.py —— beta↔gamma 关键目录文件清单 diff"""
import os, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

for sub in ('history/units', 'history/countries', 'history/general', 'common/on_actions',
            'events', 'common/scripted_triggers', 'common/scripted_effects'):
    fb = {os.path.basename(p).lower() for p in glob.glob(os.path.join(B, *sub.split('/'), '*'))
          if os.path.isfile(p)}
    fg = {os.path.basename(p).lower() for p in glob.glob(os.path.join(G, *sub.split('/'), '*'))
          if os.path.isfile(p)}
    only_b = sorted(fb - fg)
    only_g = sorted(fg - fb)
    print(f'=== {sub}: beta {len(fb)} 个 / gamma {len(fg)} 个 ===')
    if only_b:
        print(f'  beta 有、gamma 无（{len(only_b)}）:')
        for f in only_b[:30]:
            print(f'    {f}')
    if only_g:
        print(f'  gamma 有、beta 无（{len(only_g)}）:')
        for f in only_g[:15]:
            print(f'    {f}')
    if not only_b and not only_g:
        print('  文件清单一致')
    print()

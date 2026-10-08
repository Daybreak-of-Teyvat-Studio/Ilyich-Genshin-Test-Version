# -*- coding: utf-8 -*-
"""delete_1314_all.py —— 在所有 simp_chinese loc 文件里删除 VICTORY_POINTS_1314 陈旧键（仓库+副本）
并统计各文件 VP 键的活/死构成"""
import os, re, sys, glob, json

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'localisation', 'simp_chinese')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version\localisation\simp_chinese'
br = json.load(open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), encoding='utf-8'))
LIVE = set(br['live'])

for base, tag in ((REPO, '仓库'), (DEP, '副本')):
    print(f'=== {tag} ===')
    for p in sorted(glob.glob(os.path.join(base, '*.yml'))):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        keys = [int(m.group(1)) for m in re.finditer(r'(?m)^\s*VICTORY_POINTS_(\d+):', t)]
        if not keys:
            continue
        live_n = sum(1 for k in keys if k in LIVE)
        had = 1314 in keys
        if had:
            raw = open(p, 'rb').read()
            t2 = raw.decode('utf-8-sig')
            t2, n = re.subn(r'(?m)^[ \t]*VICTORY_POINTS_1314:\d*[ \t]*"[^"]*"[ \t]*\r?\n?', '', t2)
            open(p, 'wb').write(((b'\xef\xbb\xbf' if raw[:3] == b'\xef\xbb\xbf' else b'') + t2.encode('utf-8')))
            t = t2
        t3 = open(p, encoding='utf-8-sig', errors='replace').read()
        print(f'  {os.path.basename(p)}: VP键 {len(keys)}（活 {live_n} / 死 {len(keys)-live_n}）'
              + (f' —— 删除 1314 ×{n}' if had else '')
              + ('；1314 残留!' if 'VICTORY_POINTS_1314' in t3 else ''))

# -*- coding: utf-8 -*-
"""对比 mod/原版 setup gui 的 idea 预览元素（尺寸/数量布局）"""
import os, io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
o = []
for label, root in [('mod', G), ('原版', V)]:
    t = io.open(os.path.join(root, 'interface', 'frontendgamesetupview.gui'), 'rb').read().decode('utf-8-sig', errors='replace')
    o.append(f'##### {label}：含 idea 的行 #####')
    lines = t.splitlines()
    for i, l in enumerate(lines):
        if re.search(r'(?i)idea', l):
            ctx = '\n'.join(x.strip() for x in lines[max(0, i - 2):i + 6])
            o.append(f'  [{i+1}] {l.strip()[:120]}')
            o.append(f'      上下文: {ctx[:400]}')
            o.append('')
print('\n'.join(o))

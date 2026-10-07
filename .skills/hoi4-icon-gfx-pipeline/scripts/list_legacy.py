# -*- coding: utf-8 -*-
"""列出 23 张历史遗留（非本批生成、尺寸不符、未收录进 gfx）。"""
import os, re
from PIL import Image

MOD = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
TAGS = ['LYY', 'MOT', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
FOLDER = {'goal': 'goals', 'idea': 'ideas'}
SPEC = {'goal': (96, 87), 'idea': (64, 64)}

n = 0
for tag in TAGS:
    for kind in ('goal', 'idea'):
        d = os.path.join(MOD, 'gfx', 'interface', FOLDER[kind], tag)
        pat = re.compile(r'^%s_%s_[A-Za-z0-9_]+\.png$' % (kind, tag))
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if not os.path.isfile(p) or not fn.lower().endswith('.png'):
                continue
            if pat.match(fn):
                sz = Image.open(p).size
                if sz != SPEC[kind]:
                    n += 1
                    print('%-4s %-5s %-44s %s' % (tag, kind, fn, sz))
            else:
                n += 1
                try:
                    sz = Image.open(p).size
                except Exception:
                    sz = '?'
                print('%-4s %-5s %-44s %s' % (tag, kind, fn, sz))
print('\n合计 %d 个历史遗留文件（未被任何新 gfx 引用）' % n)
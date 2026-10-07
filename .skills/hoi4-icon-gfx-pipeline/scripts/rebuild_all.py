# -*- coding: utf-8 -*-
"""补齐：确保 8 国 16 个目录各有 200 goal + 200 idea 规范名 PNG。

幂等：已存在就跳过（并校验内容与权威源一致）。
"""
import os, re, shutil, hashlib, sys, importlib
from PIL import Image
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen")

MOD = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
GEN = r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen"
TAGS = ['LYY', 'MOT', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
FOLDER = {'goal': 'goals', 'idea': 'ideas'}
SPEC = {'goal': (96, 87), 'idea': (64, 64)}


def nz(s):
    return re.sub(r'_+', '_', s.replace(' ', '_')).strip('_')


def body_of(fn, kind):
    stem = os.path.splitext(fn)[0]
    stem = re.sub(r'^(goal|idea)_', '', stem)
    p = stem.split('_', 1)
    if len(p) == 2 and p[0].upper() in TAGS:
        stem = p[1]
    if kind == 'idea':
        stem = re.sub(r'^Idea_', '', stem)
    return nz(stem)


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


tot_new = tot_bad = 0
for tag in TAGS:
    for kind in ('goal', 'idea'):
        folder = FOLDER[kind]
        dst_dir = os.path.join(MOD, 'gfx', 'interface', folder, tag)
        new = bad = skip = 0
        for ver in ('v7', 'v8'):
            sd = os.path.join(GEN, 'out_%s_%s' % (tag, ver), kind)
            if not os.path.isdir(sd):
                continue
            for fn in sorted(os.listdir(sd)):
                if not fn.lower().endswith('.png'):
                    continue
                body = body_of(fn, kind)
                norm = '%s_%s_%s.png' % (kind, tag, body)
                sp, dp = os.path.join(sd, fn), os.path.join(dst_dir, norm)
                if os.path.exists(dp):
                    if md5(sp) != md5(dp):
                        bad += 1
                        print('! 内容不符 %s/%s/%s' % (folder, tag, norm))
                    skip += 1
                    continue
                try:
                    shutil.copyfile(sp, dp)
                    sz = Image.open(dp).size
                    if sz != SPEC[kind]:
                        print('! 尺寸异常 %s/%s/%s %s' % (folder, tag, norm, sz))
                    new += 1
                except Exception as e:
                    bad += 1
                    print('! 复制失败 %s : %s' % (norm, e))
        # 复核最终数量
        pat = re.compile(r'^%s_%s_[A-Za-z0-9_]+\.png$' % (kind, tag))
        n = sum(1 for f in os.listdir(dst_dir) if pat.match(f))
        print('%-6s/%s  新建%3d  已存在%3d  异常%3d  => 规范名 %d'
              % (folder, tag, new, skip, bad, n))
        tot_new += new; tot_bad += bad
print('\n共新建 %d，异常 %d' % (tot_new, tot_bad))
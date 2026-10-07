# -*- coding: utf-8 -*-
"""最终验收：8 国图标 + gfx 全量检查。"""
import os, re, collections
from PIL import Image

MOD = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
TAGS = ['LYY', 'MOT', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
FOLDER = {'goal': 'goals', 'idea': 'ideas'}
SPEC = {'goal': (96, 87), 'idea': (64, 64)}

NAME_RE = re.compile(r'^(goal|idea)_([A-Za-z0-9]+)_([A-Za-z0-9_]+)\.png$')
TEX_RE = re.compile(r'^\t\ttexturefile = "([^"]+)"$', re.M)
ANIMMASK_RE = re.compile(r'^\t\t\tanimationmaskfile = "([^"]+)"$', re.M)
SPRITE_RE = re.compile(r'^\t\tname = "([^"]+)"$', re.M)
SHINE_RE = re.compile(r'^\t\tname = "(.+)_shine"$', re.M)

errs = collections.Counter()
detail = collections.defaultdict(list)

# ---------- 1. 目录 ----------
for tag in TAGS:
    for kind in ('goal', 'idea'):
        key = '%s/%s' % (FOLDER[kind], tag)
        d = os.path.join(MOD, 'gfx', 'interface', FOLDER[kind], tag)
        pat = re.compile(r'^%s_%s_[A-Za-z0-9_]+\.png$' % (kind, tag))
        names, badsize, others, legacy = [], [], [], []
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if not os.path.isfile(p):
                continue
            if not fn.lower().endswith('.png'):
                others.append(fn)
                continue
            if not pat.match(fn):
                others.append(fn)
                continue
            names.append(fn)
            if Image.open(p).size != SPEC[kind]:
                badsize.append(fn)
        if len(names) != 200:
            errs['规范名数量!=200'] += 1
            detail['规范名数量!=200'].append('%s: %d' % (key, len(names)))
        for f in badsize:
            errs['尺寸异常'] += 1
            detail['尺寸异常'].append('%s/%s' % (key, f))
        for f in others:
            low = f.lower()
            if low.endswith('.dds') or low == 'desktop.ini':
                legacy.append(f)                # 2022 年原版遗留，保留
            else:
                errs['非规范名残留'] += 1
                detail['非规范名残留'].append('%s/%s' % (key, f))
        detail.setdefault('历史遗留(保留)', [])
        for f in legacy:
            detail['历史遗留(保留)'].append('%s/%s' % (key, f))
        # 子文件夹
        sub = [x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x))]
        if sub:
            errs['目录内有子文件夹'] += 1
            detail['目录内有子文件夹'].append('%s: %s' % (key, sub))

# ---------- 2. 单数目录 ----------
sing = [x for x in os.listdir(os.path.join(MOD, 'gfx', 'interface'))
        if x in ('goal', 'idea')]
if sing:
    errs['单数目录残留'] += len(sing)
    detail['单数目录残留'] = sing

# ---------- 3. gfx ----------
for tag in TAGS:
    g = os.path.join(MOD, 'interface', 'DOT_Icons_%s.gfx' % tag)
    if not os.path.exists(g):
        errs['gfx 缺失'] += 1
        detail['gfx 缺失'].append(tag)
        continue
    txt = open(g, encoding='utf-8').read()
    # 括号
    if txt.count('{') != txt.count('}'):
        errs['括号不平衡'] += 1
        detail['括号不平衡'].append('%s: %d{ %d}' % (tag, txt.count('{'), txt.count('}')))
    names = SPRITE_RE.findall(txt)
    texs = TEX_RE.findall(txt)
    shines = SHINE_RE.findall(txt)
    # 唯一性
    dup = [k for k, v in collections.Counter(names).items() if v > 1]
    if dup:
        errs['sprite 名重复'] += len(dup)
        detail['sprite 名重复'] += ['%s/%s' % (tag, x) for x in dup[:5]]
    # 命名规范：GFX_<kind>_<TAG>_<body>[_shine]
    badname = [n for n in names
               if not re.match(r'^GFX_(goal|idea)_%s_[A-Za-z0-9_]+(_shine)?$' % tag, n)]
    if badname:
        errs['sprite 名不符格式'] += len(badname)
        detail['sprite 名不符格式'] += ['%s/%s' % (tag, x) for x in badname[:5]]
    # 数量
    plain = [n for n in names if not n.endswith('_shine')]
    idea_plain = [n for n in plain if n.startswith('GFX_idea_')]
    goal_plain = [n for n in plain if n.startswith('GFX_goal_')]
    goal_shine = [n for n in names if n.endswith('_shine')]
    if len(goal_plain) != 200:
        errs['goal sprite 数!=200'] += 1
        detail['goal sprite 数!=200'].append('%s: %d' % (tag, len(goal_plain)))
    if len(idea_plain) != 200:
        errs['idea sprite 数!=200'] += 1
        detail['idea sprite 数!=200'].append('%s: %d' % (tag, len(idea_plain)))
    if len(goal_shine) != 200:
        errs['goal shine 数!=200'] += 1
        detail['goal shine 数!=200'].append('%s: %d' % (tag, len(goal_shine)))
    if any(n.startswith('GFX_idea_') and n.endswith('_shine') for n in names):
        errs['idea 不该有 shine'] += 1
        detail['idea 不该有 shine'].append(tag)
    # shine 配对
    gp = set(x[:-6] for x in goal_shine)
    if gp != set(goal_plain):
        errs['shine 配对不齐'] += 1
        detail['shine 配对不齐'].append(tag)
    # texturefile 路径有效性
    miss = []
    for t in set(texs):
        if not os.path.exists(os.path.join(MOD, t.replace('/', os.sep))):
            miss.append(t)
    if miss:
        errs['texturefile 路径失效'] += len(miss)
        detail['texturefile 路径失效'] += ['%s/%s' % (tag, x) for x in miss[:5]]
    # animationmaskfile 有效性
    mmiss = [t for t in set(ANIMMASK_RE.findall(txt))
             if not os.path.exists(os.path.join(MOD, t.replace('/', os.sep)))]
    if mmiss:
        errs['animationmaskfile 失效'] += len(mmiss)
        detail['animationmaskfile 失效'] += ['%s/%s' % (tag, x) for x in mmiss[:5]]
    # texturefile 必须是大写规范名
    badtex = [t for t in set(texs)
              if not re.search(r'^gfx/interface/(goals|ideas)/%s/(goal|idea)_%s_[A-Za-z0-9_]+\.png$'
                               % (tag, tag), t)]
    if badtex:
        errs['texturefile 非规范名'] += len(badtex)
        detail['texturefile 非规范名'] += ['%s/%s' % (tag, x) for x in badtex[:5]]

print('=' * 62)
print('最终验收')
print('=' * 62)
if not errs:
    print('\n★ 全部通过：8 国 × (200 goal + 200 idea) 图标，')
    print('  goal 200 普通 + 200 shine，idea 200 普通（无 shine），')
    print('  sprite 名 / texturefile / animationmaskfile 全部有效。')
else:
    tot = sum(errs.values())
    print('\n共 %d 类问题，合计 %d 处' % (len(errs), tot))
    for k, v in errs.most_common():
        print('\n[%s] %d 处' % (k, v))
        for x in detail[k][:8]:
            print('    %s' % x)
        if len(detail[k]) > 8:
            print('    ... 共 %d 条' % len(detail[k]))
    print('\n=== 有问题国家数: %d / 8 ===' % len(set(
        x.split('/')[0] for k in detail
        if k != '历史遗留(保留)' for x in detail[k])))
print('\n历史遗留文件（未收录进 gfx，保留原样）: %d 个'
      % len(detail.get('历史遗留(保留)', [])))
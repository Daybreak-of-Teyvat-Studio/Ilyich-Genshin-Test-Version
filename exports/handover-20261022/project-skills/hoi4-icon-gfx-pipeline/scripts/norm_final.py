# -*- coding: utf-8 -*-
"""最终规范化 + gfx 生成（一次性做对）。

命名口径（用户 2026-10-04 最终确认）：
  goal : goal_<TAG>_<英文名>.png          例 goal_LYY_Jade_Workshop.png
  idea : idea_<TAG>_<英文名>.png          例 idea_LYY_Alchemy_Bench.png
         ↑ 不再有 idea_<TAG>_Idea_<英文名> 里重复的 'Idea' 段
  英文名 = topics 名去掉 <Tag> 段、去掉 idea 的 'Idea' 段、压连续下划线

gfx 口径：
  goal -> 普通 SpriteType + _shine SpriteType
  idea -> 只要普通 SpriteType（用户明确 idea 不要 shine）

权威源：out_<TAG>_v7（第一批）+ out_<TAG>_v8（第二批）
本脚本只复制到新名+输出待删清单，不删不改已存在文件。
"""
import os, re, shutil, json, importlib, sys
from PIL import Image
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen")

MOD = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
GEN = r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen"
OUT = os.path.join(GEN, 'stage4')
TAGS = ['LYY', 'MOT', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
FOLDER = {'goal': 'goals', 'idea': 'ideas'}
SPEC = {'goal': (96, 87), 'idea': (64, 64)}
os.makedirs(OUT, exist_ok=True)


def nz(s):
    return re.sub(r'_+', '_', s.replace(' ', '_')).strip('_')


def body_of(fn, kind):
    """从任意源文件名提取「英文名」并规范化。
    idea 的 'Idea' 段会被剥掉（第一批 v7 文件是 <Tag>_Idea_X，第二批 v8 是 idea_<Tag>_Idea_X）
    """
    stem = os.path.splitext(fn)[0]
    # 去掉 kind 前缀
    stem = re.sub(r'^(goal|idea)_', '', stem)
    # 去掉 tag 段（大小写不敏感）
    parts = stem.split('_', 1)
    if len(parts) == 2 and parts[0].upper() in TAGS:
        stem = parts[1]
    else:
        stem = stem                       # 无 tag 段，原样
    if kind == 'idea':
        stem = re.sub(r'^Idea_', '', stem)
    return nz(stem)


# ---------- 1. 落地 PNG ----------
rm_old = []
rows = []
for tag in TAGS:
    for kind in ('goal', 'idea'):
        folder = FOLDER[kind]
        dst_dir = os.path.join(MOD, 'gfx', 'interface', folder, tag)
        seen = {}
        for ver in ('v7', 'v8'):
            sd = os.path.join(GEN, 'out_%s_%s' % (tag, ver), kind)
            if not os.path.isdir(sd):
                continue
            for fn in sorted(os.listdir(sd)):
                if not fn.lower().endswith('.png'):
                    continue
                body = body_of(fn, kind)
                norm = '%s_%s_%s.png' % (kind, tag, body)
                if norm in seen:
                    rows.append('! %s/%s 重名 %s（%s 与 %s）'
                                % (folder, tag, norm, seen[norm], ver))
                    continue
                seen[norm] = ver
                sp = os.path.join(sd, fn)
                dp = os.path.join(dst_dir, norm)
                if not os.path.exists(dp):
                    try:
                        shutil.copyfile(sp, dp)
                    except Exception as e:
                        rows.append('!复制失败 %s : %s' % (norm, e))
                else:
                    rm_old.append('gfx/interface/%s/%s/%s' % (folder, tag, fn))
        rows.append('%-6s/%s  规范名 %d' % (folder, tag, len(seen)))

for r in rows:
    print(r)
print()

# ---------- 2. 待删清单：所有非规范名的 png ----------
for tag in TAGS:
    for kind in ('goal', 'idea'):
        folder = FOLDER[kind]
        d = os.path.join(MOD, 'gfx', 'interface', folder, tag)
        keep = set()
        for ver in ('v7', 'v8'):
            sd = os.path.join(GEN, 'out_%s_%s' % (tag, ver), kind)
            if not os.path.isdir(sd):
                continue
            for fn in os.listdir(sd):
                if fn.lower().endswith('.png'):
                    keep.add('%s_%s_%s.png'
                             % (kind, tag, body_of(fn, kind)))
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith('.png'):
                continue
            if fn not in keep:
                rm_old.append('gfx/interface/%s/%s/%s' % (folder, tag, fn))

# 去重保序
seen = set()
rm_list = []
for x in rm_old:
    if x not in seen:
        seen.add(x)
        rm_list.append(x)
with open(os.path.join(OUT, '_rm_norm_final.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(rm_list) + '\n')
print('待删（非规范名 PNG）%d 条 -> stage4/_rm_norm_final.txt' % len(rm_list))
json.dump(rm_list, open(os.path.join(OUT, '_rm_norm_final.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False)
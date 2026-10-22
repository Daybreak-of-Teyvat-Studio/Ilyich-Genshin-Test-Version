# -*- coding: utf-8 -*-
"""最终 gfx 生成：goal 有 shine，idea 无 shine（用户 2026-10-04 明确）。

只收录规范名 PNG（goal_<TAG>_<名>.png / idea_<TAG>_<名>.png），
不收录历史遗留（.dds、无 tag 段、尺寸不符、小写 tag）。
输出 stage4/DOT_Icons_<TAG>.gfx，落地用 Bash rm -f + cat >。
"""
import os, re, json
from PIL import Image

MOD = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
OUT = r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen\stage4"
TAGS = ['LYY', 'MOT', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
FOLDER = {'goal': 'goals', 'idea': 'ideas'}
SPEC = {'goal': (96, 87), 'idea': (64, 64)}
os.makedirs(OUT, exist_ok=True)

ANIM = ('\t\t\tanimationmaskfile = "{mask}"\n'
        '\t\t\tanimationtexturefile = "gfx/interface/{folder}/shine_overlay.dds"\n'
        '\t\t\tanimationrotation = {rot}\n'
        '\t\t\tanimationlooping = no\n'
        '\t\t\tanimationtime = 0.75\n'
        '\t\t\tanimationdelay = 0\n'
        '\t\t\tanimationblendmode = "add"\n'
        '\t\t\tanimationtype = "scrolling"\n'
        '\t\t\tanimationrotationoffset = {{ x = 0.0 y = 0.0 }}\n'
        '\t\t\tanimationtexturescale = {{ x = 1.0 y = 1.0 }}\n')

summary, skipped_all = [], {}
for tag in TAGS:
    lines = ['spriteTypes = {']
    names, cnt, skipped = set(), {'goal': 0, 'idea': 0, 'shine': 0}, []
    for kind in ('goal', 'idea'):
        folder = FOLDER[kind]
        d = os.path.join(MOD, 'gfx', 'interface', folder, tag)
        pat = re.compile(r'^%s_%s_([A-Za-z0-9_]+)\.png$' % (kind, tag))
        cand = []
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if not os.path.isfile(p):
                continue
            if not fn.lower().endswith('.png'):
                continue
            m = pat.match(fn)                 # 严格：tag 段必须全大写
            if not m:
                skipped.append(fn)
                continue
            body = re.sub(r'_+', '_', m.group(1)).strip('_')
            try:
                sz = Image.open(p).size
            except Exception:
                skipped.append(fn + '(读不出)')
                continue
            if sz != SPEC[kind]:
                skipped.append('%s %s' % (fn, sz))   # 尺寸不符 = 遗留
                continue
            cand.append((body, fn))
        cand.sort()

        for body, fn in cand:
            nm = 'GFX_%s_%s_%s' % (kind, tag, body)
            if nm in names:
                continue
            names.add(nm)
            tex = 'gfx/interface/%s/%s/%s' % (folder, tag, fn)

            lines.append('\tSpriteType = {')
            lines.append('\t\tname = "%s"' % nm)
            lines.append('\t\ttexturefile = "%s"' % tex)
            lines.append('\t}')

            if kind == 'goal':                # 只有 goal 要 shine
                lines.append('\tSpriteType = {')
                lines.append('\t\tname = "%s_shine"' % nm)
                lines.append('\t\ttexturefile = "%s"' % tex)
                lines.append('\t\teffectFile = "gfx/FX/buttonstate.lua"')
                for rot in ('-90.0', '90.0'):
                    lines.append('\t\tanimation = {')
                    lines.append(ANIM.format(mask=tex, folder=folder,
                                             rot=rot).rstrip('\n'))
                    lines.append('\t\t}')
                lines.append('\t\tlegacy_lazy_load = no')
                lines.append('\t}')
                cnt['shine'] += 1
            cnt[kind] += 1

    lines.append('}')
    text = '\n'.join(lines) + '\n'
    depth = text.count('{') - text.count('}')
    with open(os.path.join(OUT, 'DOT_Icons_%s.gfx' % tag), 'w',
              encoding='utf-8', newline='\r\n') as f:
        f.write(text)
    skipped_all[tag] = skipped
    summary.append((tag, cnt['goal'], cnt['idea'], cnt['shine'],
                    len(names), depth))

print('=== 最终 gfx（goal 有 shine / idea 无 shine）===')
print('%-5s %6s %6s %7s %8s %6s' % ('TAG', 'goal', 'idea', 'shine',
                                     'sprite', 'depth'))
bad = 0
for tag, g, i, s, n, depth in summary:
    ok = (g == 200 and i == 200 and depth == 0 and s == 200)
    if not ok:
        bad += 1
    print('%-5s %6d %6d %7d %8d %6d%s'
          % (tag, g, i, s, n, depth, '' if ok else '  <- 异常'))
print('\n异常国家: %d / 8' % bad)
tot = sum(len(v) for v in skipped_all.values())
print('未收录文件合计 %d（历史遗留/旧命名，不进 gfx）' % tot)
for tag in TAGS:
    if skipped_all[tag]:
        print('  %s: %s' % (tag, '; '.join(skipped_all[tag][:6])))
json.dump(skipped_all, open(os.path.join(OUT, 'skipped.json'), 'w',
                            encoding='utf-8'), ensure_ascii=False, indent=1)
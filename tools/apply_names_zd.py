# -*- coding: utf-8 -*-
"""apply_names_zd.py —— 至冬 11 条州名（覆盖语义，旧名变更会报告）"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES_F = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'localisation', 'simp_chinese',
                       'DOT_state_names_gamma_l_simp_chinese.yml')
NAMES = [(320, '凝露镇'), (312, '巡猎者木屋'), (7, '海屑镇'), (281, '焰羽谷'),
         (212, '曙光车站'), (186, '至冬宫'), (182, '格鲁波夫'), (240, '至冬堡'),
         (228, '【冬契军】总部'), (260, '科洛列夫茨基剧院'), (239, '列车总站')]

raw = open(NAMES_F, 'rb').read()
has_bom = raw[:3] == b'\xef\xbb\xbf'
t = raw.decode('utf-8-sig')
nl = '\r\n' if '\r\n' in t else '\n'
nm_map = dict(NAMES)
out, changed, confirmed, warns = [], 0, 0, []
for l in t.split(nl):
    m = re.match(r'^(\s*DOT_STATE_(\d+):)0?(\s*)"([^"]*)"', l)
    if m and int(m.group(2)) in nm_map:
        sid = int(m.group(2))
        want = nm_map[sid]
        cur = m.group(4)
        if cur == want:
            confirmed += 1
        elif cur == '*':
            l = f'{m.group(1)}0{m.group(3)}"{want}"'
            changed += 1
        else:
            print(f'  s{sid}: 「{cur}」→「{want}」（覆盖旧名）')
            l = f'{m.group(1)}0{m.group(3)}"{want}"'
            changed += 1
    out.append(l)
open(NAMES_F, 'wb').write(((b'\xef\xbb\xbf' if has_bom else b'') + nl.join(out).encode('utf-8')))
print(f'写入 {changed}，确认 {confirmed}，共 {changed + confirmed}/{len(NAMES)}')

# 回读验证
t2 = open(NAMES_F, encoding='utf-8-sig').read()
bad = [(s, n) for s, n in NAMES
       if re.search(rf'DOT_STATE_{s}:0\s*"{re.escape(n)}"', t2) is None]
print('验证:', '全部 ✓' if not bad else f'✗ {bad}')

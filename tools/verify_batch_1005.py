# -*- coding: utf-8 -*-
"""verify_batch_1005.py —— 10-05 批次独立复验（转省 + 州名15 + VP7）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
MOD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
NAMES_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VP_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
NAMES = [(735, '漫曛谷'), (765, '焚风试炼处'), (722, '荧草窟'), (817, '沃陆之邦'),
         (809, '【石火坠陨处】'), (830, '孑遗的留迹'), (804, '觐山古道'),
         (803, '流火的实验地'), (837, '天火之冠'), (81, '刺梨岩'), (552, '呼呼丘'),
         (558, '彩彩崖'), (603, '悠悠集市'), (550, '浪浪湾'), (526, '提提岛')]
VPS = [(606, '谜土祭祀场', 15), (4310, '茜特菈莉的住处', 15), (1492, '飞行试炼场', 15),
       (1137, '远古圣山', 25), (917, '卡萨扎莱宫', 15), (1739, '天火之冠', 15),
       (795, '隐匿的谜土', 15)]

p2s, vp_all = {}, {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        p2s[int(x)] = sid
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        xs = vm.group(1).split()
        for i in range(0, len(xs) - 1, 2):
            vp_all[(sid, int(xs[i]))] = int(xs[i + 1])

errs = 0
# 转省
print(f"p2192 -> s{p2s.get(2192)}（应 722）{'✓' if p2s.get(2192) == 722 else '✗'}")
errs += p2s.get(2192) != 722
# 州名
nm_t = open(NAMES_F, encoding='utf-8-sig').read()
for sid, nm in NAMES:
    ok = re.search(rf'DOT_STATE_{sid}:0\s*"{re.escape(nm)}"', nm_t) is not None
    errs += not ok
    if not ok:
        print(f'  ✗ s{sid}「{nm}」缺失')
print(f'州名 15 条: {"全部 ✓" if not any(re.search(rf"DOT_STATE_{s}:0\s*\"{re.escape(n)}\"", nm_t) is None for s, n in NAMES) else "有缺失"}')
# VP
vp_t = open(VP_F, encoding='utf-8-sig').read()
for pid, nm, val in VPS:
    h = p2s.get(pid)
    ok_v = vp_all.get((h, pid)) == val if h else False
    ok_l = re.search(rf'VICTORY_POINTS_{pid}:0\s*"{re.escape(nm)}"', vp_t) is not None
    errs += not (ok_v and ok_l)
    print(f'  VP p{pid}「{nm}」{val}: s{h} 值{"✓" if ok_v else "✗"} 本地化{"✓" if ok_l else "✗"}')
print('\n全部通过 ✓' if errs == 0 else f'\n{errs} 项失败 ✗')

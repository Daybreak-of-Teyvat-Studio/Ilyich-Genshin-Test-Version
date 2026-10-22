# -*- coding: utf-8 -*-
"""verify_natlan_theory.py —— 验证"州名被写成省号所在州"理论 + 查批次前备份的原始值"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
BK1 = os.path.join(ROOT, '.backups', 'names_natlan_20261003_224721')
BK2 = os.path.join(ROOT, '.backups', 'names_natlan2_20261003_231429')

PAIRS = [  # (指令州号, 实际写入州号, 名字)
    (782, 28, '燃素开采研究所'), (814, 110, '窃火者密岛'), (106, 214, '玉裙之丘'),
    (828, 274, '溶水域'), (747, 343, '烟谜主'), (766, 410, '彩石顶'),
    (105, 423, '浮土静界'), (781, 595, '悬木人'), (643, 613, '圣火竞技场'),
    (810, 645, '流泉之众'), (1379, 720, '柴薪之丘'), (767, 742, '祖遗庙宇')]

# 当前 省→州 映射
p2s = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    for x in (pm.group(1).split() if pm else []):
        p2s[int(x)] = sid

print('=== 理论验证：指令州号被当作省号解析 → 写到了该省所在州 ===')
for sid, wrote, nm in PAIRS:
    host = p2s.get(sid)
    mark = '✓' if host == wrote else '✗'
    print(f'  {mark} {nm}: 指令 {sid} → 写入 {wrote}（省{sid}现在在 s{host}）' if host else
          f'  {mark} {nm}: 指令 {sid} → 写入 {wrote}（省{sid}不存在）')

def loc_of(bdir):
    out = {}
    for p in glob.glob(os.path.join(bdir, '**', '*.yml'), recursive=True):
        for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"',
                             open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
            out[int(m.group(1))] = m.group(2)
    return out

print()
print('=== 批次前备份里，12 个错号原本的名字 / 12 个正确州号原本的名字 ===')
b1 = loc_of(BK1) if os.path.isdir(BK1) else {}
b2 = loc_of(BK2) if os.path.isdir(BK2) else {}
for sid, wrote, nm in PAIRS:
    print(f'  {nm}: 错号 s{wrote} 批次前={b1.get(wrote, "(无key)")!r} / natlan2前={b2.get(wrote, "(无key)")!r}'
          f'  |  正确号 s{sid} 批次前={b1.get(sid, "(无key)")!r} / natlan2前={b2.get(sid, "(无key)")!r}')

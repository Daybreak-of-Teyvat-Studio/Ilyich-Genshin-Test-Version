# -*- coding: utf-8 -*-
"""
州名本地化改造：
  · 861 个州 name key 唯一化（STATE_<id>）
  · 本地化全部设 "*" 占位
  · 用户指定的 15 州设中文名
  · 写入新文件 DOT_state_names_gamma_l_simp_chinese.yml（BOM+CRLF）
  · state 文件的 name 行替换（保留注释）
"""
import os, re, sys, shutil, datetime, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
LOC = os.path.join(G, 'localisation', 'simp_chinese')

# 用户指定的 15 个省号 → 州 → 中文名
NAMED = [(1466, '蒙德城'), (451, '低语森林'), (464, '摘星崖'), (474, '千风神殿'),
         (484, '风起地'), (424, '望风角'), (454, '星落湖'), (435, '鹰翔海滩'),
         (422, '望风山地'), (412, '风车镇'), (437, '明冠峡'), (505, '誓言岬'),
         (64, '马斯克礁'), (483, '清泉镇'), (500, '晨曦酒庄')]

s2p = {}
for f in os.listdir(ST):
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}

names = {sid: '*' for sid in s2p}
for pid, cn in NAMED:
    s = p2s.get(pid)
    assert s, f'省 {pid} 不在任何州'
    names[s] = cn
    print(f'  省 {pid} → 州 {s} = {cn}')

# state 文件 name 行替换
bdir = os.path.join(ROOT, '.backups', 'state_names_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
n = 0
for sid, ps in s2p.items():
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = open(fp, encoding='utf-8-sig', newline='').read()
    t2 = re.sub(r'(\bname\s*=\s*)"([^"]*)"', rf'\1"STATE_{sid}"', t, count=1)
    if t2 != t:
        with open(fp, 'w', encoding='utf-8', newline='') as fh:
            fh.write(t2)
        n += 1
print(f'state 文件 name 行唯一化 {n} 个')

# 本地化文件
lp = os.path.join(LOC, 'DOT_state_names_gamma_l_simp_chinese.yml')
lines = ['l_simp_chinese:']
for sid in sorted(names):
    lines.append(f' STATE_{sid}:0 "{names[sid]}"')
open(lp, 'wb').write(('\r\n'.join(lines) + '\r\n').encode('utf-8'))
print(f'本地化文件已写: {lp}（{len(names)} 条）')

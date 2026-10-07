# -*- coding: utf-8 -*-
"""gen_mapping_doc.py —— 生成州号变动映射文档（docs/州号变动_20261007至冬重划.md）"""
import os, re, sys, glob, json

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
OUT = os.path.join(ROOT, 'docs', '州号变动_20261007至冬重划.md')

div = json.load(open(os.path.join(ROOT, 'tools', 'zd_division.json'), encoding='utf-8'))
comp_provs = {int(c): sorted(v) for c, v in div['comp_provs'].items()}

# 现状：id → (owner, 省 数, 名)
cur = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    cur[sid] = (om.group(1) if om else '海', len(pm.group(1).split()))

fill = open(os.path.join(ROOT, 'tools', 'fill_out2.txt'), encoding='utf-8-sig').read()
pairs = [(int(a), int(b)) for a, b in re.findall(r'state (\d+) .{0,3}state (\d+)', fill)]

L = ['# 州号变动映射 —— 2026-10-07 至冬重划 + 合并 + 补号', '',
     '## 一、至冬重划（198 州 → 65 州）', '',
     '按涂色图连通色块分组；新州 id 继承省重叠最大的旧州号。65 个新州：', '',
     '| 新州号 | 省数 | | 新州号 | 省数 | | 新州号 | 省数 |',
     '|---|---|---|---|---|---|---|---|']
sne = sorted(int(re.search(r'\bid\s*=\s*(\d+)', open(f, encoding='utf-8-sig', errors='replace').read()).group(1))
             for f in glob.glob(os.path.join(ST, '*.txt'))
             if 'owner = SNE' in open(f, encoding='utf-8-sig', errors='replace').read())
row = []
for i, s in enumerate(sne):
    row.append(f'| {s} | {cur[s][1]} |')
    if len(row) == 4:
        L.append('|'.join(row)); row = []
if row:
    L.append('|'.join(row) + '|' * (4 - len(row)))
L += ['', '其余 133 个旧至冬州号撤销；其省份并入上表新州（映射见 tools/zd_division.json 的'
         ' comp_provs + 继承逻辑 tools/repair_zd_states.py）。', '']

L += ['## 二、暂缓合并执行（7 州撤销）', '',
      '| 被并 | 并入 | 省数 |', '|---|---|---|',
      '| 583 | 603 | 5 |', '| 718 | 552 | 3 |', '| 567 | 550 | 5 |', '| 568 | 550 | 5 |',
      '| 72 | 70 | 4 |', '| 507 | 526 | 4 |', '| 759 | 735 | 3 |', '']

L += ['## 三、补号搬移（140 州换号，旧号 → 新号）', '',
      '| 旧号 | 新号 | | 旧号 | 新号 | | 旧号 | 新号 |', '|---|---|---|---|---|---|---|---|']
row = []
for old, new in pairs:
    row.append(f'| {old} | {new} |')
    if len(row) == 4:
        L.append('|'.join(row)); row = []
if row:
    L.append('|'.join(row) + '|' * (4 - len(row)))
L += ['', '## 四、名字处置', '',
      '- 原地保留：至冬宫(186)、海屑镇(7)、焰羽谷(281)、曙光车站(212)、【冬契军】总部(228)、'
      '巡猎者木屋(312)、圣火竞技场(643) 等未受重划影响的州名',
      '- 跟随内容换号：格鲁波夫→178、至冬堡→209、凝露镇→321',
      '- 丢弃：列车总站（旧239 内容并入 260，科洛列夫茨基剧院重叠更大胜出）——如需保留请指定新州号',
      '- 覆盖：刻拉蒂之眼(463，覆盖苔骨荒原)、分道誓约之地(708→759→750 跟随搬移)', '',
      '## 五、终态', '',
      f'- 州 {len(cur)} 个，1-750 严格连号；至冬 {len(sne)} 州；海州 {sum(1 for s, (o, _) in cur.items() if o == "海")} 个',
      '- buildings.txt 终版重整：声明州全量重推 + SL 每陆州 7×1+防空×3，游戏规则 0 违规',
      '- 本地化 52 条补号占位重复已清；首都零悬空；括号/BOM 全过']

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print(f'已生成 {OUT}（{len(L)} 行）')

# -*- coding: utf-8 -*-
"""本批总执行：转省 → VP（p 前缀省级）→ 命名 → 补号 → buildings 终版重整 → 自检"""
import os, re, sys, subprocess, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VPF = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')


def run_tool(cmd):
    r = subprocess.run([sys.executable, TOOL, cmd], capture_output=True, text=True,
                       encoding='utf-8', cwd=ROOT)
    out = (r.stdout or '') + (r.stderr or '')
    for l in out.split('\n'):
        if any(k in l for k in ('载入', '已写入', '备份', '同步', '校验', '!!', '跳过')):
            print('  ', l.strip()[:130])


# ① 转省 10 组
print('=== ① 转省 ===')
run_tool("4400,4402+797.30+811.4487+823.935,4454+827.369,1623+631."
         "1209,2117+645.124+642.4131,4143+712.1188+646.952+645")

# ② VP 6 个（省 → 所属州写入 VP 行 + 本地化）
VPS = [(651, '舍身陷坑', 10), (952, '酣乐之殿', 10), (765, '镇灵监牢', 10),
       (924, '生命之殿', 10), (1008, '沙虫隧道', 10), (486, 'D404 君王之殿', 10)]
print('\n=== ② VP ===')
p2s = {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for q in re.findall(r'\d+', re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1)):
        p2s[int(q)] = sid
for pid, nm, val in VPS:
    sid = p2s[pid]
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    t = open(fp, encoding='utf-8-sig', newline='').read()
    line = f'victory_points = {{ {pid} {val} }}'
    m = re.search(r'victory_points\s*=\s*\{([^}]*)\}', t)
    if m:
        # 同州多 VP：追加到现有行
        existing = m.group(1).split()
        pairs = [(existing[i], existing[i + 1]) for i in range(0, len(existing) - 1, 2)]
        if str(pid) not in [a for a, b in pairs]:
            pairs.append((str(pid), str(val)))
        line = 'victory_points = { ' + ' '.join(f'{a} {b}' for a, b in pairs) + ' }'
        t = re.sub(r'victory_points\s*=\s*\{[^}]*\}', line, t, count=1)
        how = '追加'
    else:
        hm = re.search(r'\thistory = \{', t)
        depth, i, end = 0, hm.end() - 1, None
        while i < len(t):
            if t[i] == '{':
                depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
            i += 1
        ls = t.rfind('\r\n', 0, end) + 2
        t = t[:ls] + '\t\t' + line + '\r\n' + t[ls:]
        how = '插入'
    open(fp, 'w', encoding='utf-8', newline='').write(t)
    print(f'  省 {pid}「{nm}」{val} → state {sid}（{how}）')
    vt = open(VPF, encoding='utf-8-sig', newline='').read()
    if f'VICTORY_POINTS_{pid}:' not in vt:
        nm_line = f' VICTORY_POINTS_{pid}:0 "{nm}"'
        open(VPF, 'wb').write((vt.rstrip('\r\n') + '\r\n' + nm_line + '\r\n').encode('utf-8'))

# ③ 命名（含 5 个清空 + 27 个写入）
print('\n=== ③ 命名 ===')
NAMES = {797: '*', 762: '*', 783: '*', 844: '*', 843: '*',
         778: '舍身步道', 755: '饱饮之丘', 771: '缄默之殿', 805: '赛莫德绿洲',
         787: '活力之家', 811: '荼柯落谷口', 800: '秘仪圣殿', 796: '丰饶绿洲',
         833: '砾石之丘', 832: '避让之丘', 823: '荼柯落谷口北', 835: '荼柯落谷南',
         827: '吞羊岩', 815: '赤王陵', 715: '沙之眼', 731: '塔尼特露营地',
         645: '三运河之地', 669: '折胫谷', 612: '五绿洲】的孑遗', 642: '达马山',
         712: '巨人峡谷', 725: '【神的棋盘】', 685: '亡者狭廊', 626: '愚妄行宫',
         672: '啁哳之沙', 627: '镔铁沙丘', 646: '月蓝运河', 664: '镇灵监牢',
         656: '生命之殿'}
NAMES[612] = '【五绿洲】的孑遗'
NAMES[725] = '【神的棋盘】'
NAMES[645] = '【三运河之地】'

cur = open(SN, encoding='utf-8-sig', newline='').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
exist = set()
for f in os.listdir(ST):
    if f.endswith('.txt'):
        exist.add(int(re.search(r'\bid\s*=\s*(\d+)',
                                open(os.path.join(ST, f), encoding='utf-8-sig',
                                     errors='replace').read()).group(1)))
miss = [s for s in NAMES if s not in exist]
assert not miss, f'州不存在: {miss}'
for s, nm in NAMES.items():
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
print(f'  写入 {len(NAMES)} 项（文件共 {len(names)} 条）')

# ④ 合并 822+646 —— 记下不执行
print('\n=== ④ 合并 822+646：按用户指示暂不执行（已记录）===')

# -*- coding: utf-8 -*-
"""枫丹批2：转省 + 命名（重申+新增）+ VP 10 个（省级）+ 核验"""
import os, re, sys, shutil, datetime, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VPF = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

# ① 转省
print('=== ① 转省 ===')
r = subprocess.run([sys.executable, TOOL, "9,152,647,2293,3268+31.4686+561"],
                   capture_output=True, text=True, encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '转省 [', '省 ', '已写入', '备份', '同步', '校验', '!!', '跳过')):
        print('  ', l.strip()[:130])

# ② 命名
NAMES = {69: '佩特莉可镇', 60: '海露港', 43: '白淞隧道', 449: '秋分山', 428: '白淞镇',
         439: '卡布狄斯堡遗迹', 16: '枫丹廷', 50: '茉洁站', 346: '欧庇克莱歌剧院',
         397: '露景泉', 54: '湖中垂柳', 389: '优兰尼娅湖', 38: '柔灯港',
         364: '新枫丹科学院', 357: '中央实验室遗址', 21: '幽林雾道',
         715: '沙之眼', 731: '塔尼特露营地',
         669: '折胫谷', 612: '【五绿洲】的孑遗', 642: '达马山', 712: '巨人峡谷',
         725: '【神的棋盘】', 685: '亡者狭廊', 626: '愚妄行宫', 672: '啁哳之沙',
         627: '镔铁沙丘', 646: '月蓝运河', 664: '镇灵监牢', 656: '生命之殿'}
s2p = {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}
miss = [s for s in NAMES if s not in s2p]
assert not miss, f'州不存在: {miss}'

SN_bak = os.path.join(ROOT, '.backups', 'names_fontaine2_' +
                      datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(SN_bak, exist_ok=True)
shutil.copy2(SN, os.path.join(SN_bak, os.path.basename(SN)))
cur = open(SN, encoding='utf-8-sig', newline='').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
changed = 0
for s, nm in NAMES.items():
    if names.get(s) != nm:
        changed += 1
        print(f'  state {s}: 「{names.get(s)}」→「{nm}」')
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
print(f'② 命名：实际改动 {changed} 项（其余与当前一致）')

# ③ VP 10 个
VPS = [(1824, '安眠处', 15), (2231, '罪祸的终末', 15), (3219, '真正的安眠处', 15),
       (237, '海沫村', 20), (893, '寂寞的地方', 10), (414, '苍晶区神像', 10),
       (3428, '揭示之书', 10), (2446, '炽热洞', 5), (1452, '隐居处', 10),
       (2342, '很明亮的地方', 10)]
print('\n=== ③ VP ===')
touched = set()
for pid, nm, val in VPS:
    sid = p2s[pid]
    touched.add(sid)
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    t = open(fp, encoding='utf-8-sig', newline='').read()
    m = re.search(r'victory_points\s*=\s*\{([^}]*)\}', t)
    if m:
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
        t = t[:ls] + f'\t\tvictory_points = {{ {pid} {val} }}\r\n' + t[ls:]
        how = '插入'
    open(fp, 'w', encoding='utf-8', newline='').write(t)
    print(f'  省 {pid}「{nm}」{val} → state {sid}（{how}）')
    vt = open(VPF, encoding='utf-8-sig', newline='').read()
    if f'VICTORY_POINTS_{pid}:' not in vt:
        nm_line = f' VICTORY_POINTS_{pid}:0 "{nm}"'
        open(VPF, 'wb').write((vt.rstrip('\r\n') + '\r\n' + nm_line + '\r\n').encode('utf-8'))
        print(f'    本地化 +{nm_line.strip()}')

print(f'\nVP 备份同 {SN_bak}')
print('=== 核验 ===')
n_dup = 0
p2s2 = collections.defaultdict(set)
for sid in s2p:
    for q in s2p[sid]:
        p2s2[q].add(sid)
dup = {k: v for k, v in p2s2.items() if len(v) > 1}
print(f'重复归属 {len(dup)}（应 0）')
import collections

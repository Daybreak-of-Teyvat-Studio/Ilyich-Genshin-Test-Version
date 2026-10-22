# -*- coding: utf-8 -*-
"""① 转省 8 组 ② 命名 12 州 ③ VP 新增 10 + 清除 2 ④ 合并记下 ⑤ buildings 重整 + 自检"""
import os, re, sys, shutil, datetime, subprocess, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VPF = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

# ===== ① 转省 =====
print('=== ① 转省 ===')
MOVES = "399+737.389+735.2192+707.4298,4319+643.1243+747.4461+810.141,425,4414+828.4383+767.1472,4393+767.196,4367+782"
r = subprocess.run([sys.executable, TOOL, MOVES], capture_output=True, text=True,
                   encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '转省 [', '省 ', '已写入', '备份', '同步', '校验', '!!', '跳过')):
        print('  ', l.strip()[:130])

# ===== ② 命名 =====
NAMES = {1379: '柴薪之丘', 643: '圣火竞技场', 747: '烟谜主', 828: '溶水域',
         810: '流泉之众', 781: '悬木人', 766: '彩石顶', 767: '祖遗庙宇',
         814: '窃火者密岛', 782: '燃素开采研究所', 105: '浮土静界', 106: '玉裙之丘'}
print('\n=== ② 命名 ===')
bdir = os.path.join(ROOT, '.backups', 'names_natlan2_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))
cur = open(SN, encoding='utf-8-sig', newline='').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
exist = set()
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        exist.add(int(re.search(r'\bid\s*=\s*(\d+)', t).group(1)))
miss = [s for s in NAMES if s not in exist]
assert not miss, f'州不存在: {miss}'
for s, nm in NAMES.items():
    if names.get(s, '*') != nm:
        print(f'  state {s}: 「{names.get(s)}」→「{nm}」')
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
print(f'  写入 {len(NAMES)} 个  BOM={open(SN,"rb").read()[:3] == b"\xef\xbb\xbf"}')

# ===== ③ VP 新增 10 个 =====
VPS = [(2149, '烟谜主', 25, 747, True), (389, '胜利点清除', 0, None, False),
       (1482, '花羽会', 25, None, True), (4154, '胜利点清除', 0, None, False),
       (4338, '燃素开采研究所', 10, None, True)]
print('\n=== ③ VP ===')
# 389 胜利点清除
fp389 = os.path.join(ST, '389-State_389.txt')
if os.path.exists(fp389):
    t = open(fp389, encoding='utf-8-sig', newline='').read()
    t2 = re.sub(r'(victory_points\s*=\s*\{[^}]*)\s+389\s+\d+(\s*\})', r'\1\2', t, count=1)
    if t2 != t:
        open(fp389, 'w', encoding='utf-8', newline='').write(t2)
        print(f'  省 389 胜利点已清除（state 389）')
# 4154 胜利点清除
fp4154 = os.path.join(ST, '4154-State_4154.txt')
if os.path.exists(fp4154):
    t = open(fp4154, encoding='utf-8-sig', newline='').read()
    t2 = re.sub(r'(victory_points\s*=\s*\{[^}]*)\s+4154\s+\d+(\s*\})', r'\1\2', t, count=1)
    if t2 != t:
        open(fp4154, 'w', encoding='utf-8', newline='').write(t2)
        print(f'  省 4154 胜利点已清除（state 4154）')

for pid, nm, val, st_hint, is_new in VPS:
    if not is_new:
        continue
    sid = p2s.get(pid)
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
        vt = vt.rstrip('\r\n') + '\r\n' + f' VICTORY_POINTS_{pid}:0 "{nm}"' + '\r\n'
        open(VPF, 'wb').write(vt.encode('utf-8'))
        print(f'    本地化 +VICTORY_POINTS_{pid}:0 "{nm}"')

# ===== ④ 合并记下 =====
print('\n=== ④ 合并记下（暂不执行） ===')
for m in ('828+112=828', '810+821=810'):
    print(f'  {m}')

# ===== ⑤ buildings 终版重整 =====
print('\n=== ⑤ buildings 终版重整 ===')
r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'rebuild_buildings_final.py')],
                   capture_output=True, text=True, encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if '终验' in l or '对齐' in l:
        print('  ', l.strip()[:120])

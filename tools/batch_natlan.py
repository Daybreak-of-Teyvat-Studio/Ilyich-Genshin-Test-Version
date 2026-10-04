# -*- coding: utf-8 -*-
"""补做上批遗漏的 3 条转省 + 5 项命名 + 3 个 VP + 记录 3 组合并"""
import os, re, sys, shutil, datetime, subprocess, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VPF = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

# ===== ① 补做上批遗漏的 3 条转省 =====
print('=== ① 补做上批转省 ===')
MOVES1 = "4321+746.4454+811.474,4361+771.434+796"
r = subprocess.run([sys.executable, TOOL, MOVES1], capture_output=True, text=True,
                   encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '转省 [', '省 ', '已写入', '备份', '同步', '校验', '!!', '跳过')):
        print('  ', l.strip()[:130])

# ===== ② 本批转省 =====
print('\n=== ② 本批转省 ===')
MOVES2 = "313+730.112+748.112,4235,4219+748.1431+709.4185+730"
r = subprocess.run([sys.executable, TOOL, MOVES2], capture_output=True, text=True,
                   encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '转省 [', '省 ', '已写入', '备份', '同步', '校验', '!!', '跳过')):
        print('  ', l.strip()[:130])

# ===== ③ 命名 =====
print('\n=== ③ 命名 ===')
NAMES = {714: '硫晶支脉', 709: '回声之子', 748: '隆崛坡', 698: '众岩之里',
         730: '分道誓约之厅', 750: '水天丛林南', 751: '*'}

s2p, s2o = {}, {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        mo = re.search(r'\bowner\s*=\s*(\w+)', t)
        s2o[sid] = mo.group(1) if mo else None
        s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}
miss = [s for s in NAMES if s not in s2p]
assert not miss, f'州不存在: {miss}'

bdir = os.path.join(ROOT, '.backups', 'names_natlan_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))

cur = open(SN, encoding='utf-8-sig', newline='').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
changed = 0
for s, nm in NAMES.items():
    if names.get(s, '*') != nm:
        changed += 1
        print(f'  state {s}（{s2o.get(s)}）: 「{names.get(s)}」→「{nm}」')
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
raw = open(SN, 'rb').read()
print(f'③ 命名：{changed} 项改动  BOM={raw[:3] == b"\xef\xbb\xbf"}  条数={len(names)}')

# ===== ④ VP 3 个 =====
print('\n=== ④ VP ===')
VPS = [(4185, '火榴大母树', 10), (4235, '特拉佐莉的住处', 10), (313, '特拉佐莉的铸造工坊', 10)]
for pid, nm, val in VPS:
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

# ===== ⑤ 记录合并（暂不执行） =====
print('\n=== ⑤ 合并记下（暂不执行） ===')
for m in ('730+719=730', '746+670=746', '774+787=774'):
    print(f'  {m}')

# ===== ⑥ buildings 终版重整 =====
print('\n=== ⑥ buildings 终版重整 ===')
r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'rebuild_buildings_final.py')],
                   capture_output=True, text=True, encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if '终验' in l or '对齐' in l or '补缺' in l:
        print('  ', l.strip()[:120])

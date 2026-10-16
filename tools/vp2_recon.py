# -*- coding: utf-8 -*-
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
OUT = os.path.join(REPO, 'tools', 'vp2_recon_out.txt')
o = []

ENTRIES = [
    (1506, '疗养院旧址', 30), (3223, '疗养院风神像', 25), (1451, '好肉族大锅', 5), (748, '黑日族方碑', 5),
    (3657, '好睡族大殿', 5), (301, '野猪林', 5), (3349, '导光机关', 5), (894, '导光机关', 5),
]
EDIT_EXISTING = {3223: (25, '疗养院风神像')}   # 3223 改值 15→25 + 改名

sd = os.path.join(G, 'history', 'states')
p2s = {}
sinfo = {}
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    for p in m.group(1).split():
        p2s[int(p)] = sid
    ow = re.search(r'owner\s*=\s*(\w+)', t)
    vps = re.findall(r'victory_points\s*=\s*\{[^}]*\}', t)
    sinfo[sid] = (ow.group(1) if ow else None, vps, f)

o.append('=== 逐条 ===')
by_state = {}
for pid, name, val in ENTRIES:
    sid = p2s.get(pid)
    if sid is None:
        o.append(f'  ✗ p{pid} {name}: 不属于任何州！')
        continue
    owner, vps, fn = sinfo[sid]
    exist = None
    for b in vps:
        toks = b.split('{')[1].split('}')[0].split()
        for i in range(0, len(toks) - 1, 2):
            if int(toks[i]) == pid:
                exist = int(toks[i+1])
    by_state.setdefault(sid, []).append((pid, name, val, exist))
    o.append(f'  p{pid} {name}({val}): 州{sid} owner={owner} 现有VP={exist}{" （改）" if pid in EDIT_EXISTING else ""}')

o.append('')
o.append('=== 按州 ===')
for sid in sorted(by_state):
    o.append(f'  州{sid} ({sinfo[sid][2]}, owner={sinfo[sid][0]}): {[(p, n, v, e) for p, n, v, e in by_state[sid]]} 现块={sinfo[sid][1]}')

o.append('')
o.append('=== loc 冲突 ===')
for pid, name, val in ENTRIES:
    k = f'VICTORY_POINTS_{pid}'
    hits = []
    for fp in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
        tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        for l in tt.splitlines():
            if re.match(r'\s*' + k + r':', l):
                hits.append((os.path.basename(fp), l.strip()[:90]))
    o.append(f'  {k} ({name}): {hits if hits else "（无，纯新增）"}')

o.append('')
o.append('=== 重名检查（这批 6 个新名字是否已被别处占用） ===')
t = io.open(os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml'), 'rb').read().decode('utf-8-sig')
for nm in ('疗养院旧址', '疗养院风神像', '好肉族大锅', '黑日族方碑', '好睡族大殿', '野猪林', '导光机关'):
    hits = [l.strip()[:90] for l in t.splitlines() if nm in l]
    o.append(f'  {nm}: {hits if hits else "无"}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

# -*- coding: utf-8 -*-
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
OUT = os.path.join(REPO, 'tools', 'recon3_out.txt')
o = []

# A) 战略区名清单（是否已有 果酒湖 / 暗之外海）
fp = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Strategic_Region_Names_l_simp_chinese.yml')
t = io.open(fp, 'rb').read().decode('utf-8-sig')
o.append('===== 战略区名清单 =====')
for l in t.splitlines():
    s = l.strip()
    if s and not s.startswith('#'):
        o.append('  ' + s[:100])
o.append(f'  含「果酒湖」: {[l.strip()[:80] for l in t.splitlines() if "果酒湖" in l]}')
o.append(f'  含「暗之外海」: {[l.strip()[:80] for l in t.splitlines() if "暗之外海" in l]}')
# Beta 里找这两个名字
bdir = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
for pat in ('果酒湖', '暗之外海'):
    hits = []
    for f2 in glob.glob(os.path.join(bdir, 'localisation', '**', '*.yml'), recursive=True):
        tt = io.open(f2, 'rb').read().decode('utf-8-sig', errors='replace')
        for l in tt.splitlines():
            if pat in l:
                hits.append(f'{os.path.basename(f2)}: {l.strip()[:80]}')
    o.append(f'  Beta 含「{pat}」: {hits[:4] if hits else "无"}')

# B) 6 个海省
kind = {}
for line in io.open(os.path.join(G, 'map', 'definition.csv'), 'rb').read().decode('utf-8-sig', errors='replace').splitlines():
    a = line.split(';')
    if len(a) > 4 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4].strip()
o.append('')
o.append('===== 6 个海省检查 =====')
SEA = [6886, 7293, 7776, 5719, 6937, 7104]
for p in SEA:
    o.append(f'  p{p}: 存在={p in kind}, 类型={kind.get(p, "?")}')

# 当前战略区归属
srd = os.path.join(G, 'map', 'strategicregions')
regions = {}
for f in sorted(os.listdir(srd)):
    tt = io.open(os.path.join(srd, f), 'rb').read().decode('utf-8-sig')
    rid = int(re.search(r'\bid\s*=\s*(\d+)', tt).group(1))
    nm = re.search(r'name\s*=\s*"([^"]+)"', tt).group(1)
    provs = [int(x) for x in re.search(r'provinces=\{([^}]*)\}', tt, re.S).group(1).split()]
    regions[rid] = (f, nm, provs)
o.append('')
for rid, (f, nm, provs) in sorted(regions.items()):
    o.append(f'  区域{rid}: {f}, name={nm}, {len(provs)} 省')
    o.append(f'    这 6 海省在此区: {[p for p in SEA if p in provs]}')
# positions for the 6 sea provs
pos = {}
tt = io.open(os.path.join(G, 'map', 'positions.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)', tt):
    pos[int(m.group(1))] = (m.group(2), m.group(3), m.group(4))
o.append('')
for p in SEA:
    o.append(f'  p{p} positions: {pos.get(p, "无")}')

# C) 转省批次
o.append('')
o.append('===== 转省批次侦察 =====')
sd = os.path.join(G, 'history', 'states')
p2s = {}
sinfo = {}
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    tt = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', tt).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', tt, re.S)
    plist = [int(x) for x in m.group(1).split()]
    sinfo[sid] = (f, plist, tt)
    for p in plist:
        p2s[p] = sid
MOVE = {1570: 484, 1306: 435, 1960: 435, 3515: 435, 845: 500}
for p, target in MOVE.items():
    cur = p2s.get(p)
    o.append(f'  p{p} → 州{target}: 现属州={cur}（{sinfo.get(cur, ("?",))[0] if cur else "无"}）, 目标州存在={target in sinfo}')
    if cur and cur in sinfo:
        tt = sinfo[cur][2]
        vb = re.findall(r'victory_points\s*=\s*\{[^}]*\}', tt)
        own = None
        for b in vb:
            tk = b.split('{')[1].split('}')[0].split()
            for i in range(0, len(tk) - 1, 2):
                if int(tk[i]) == p:
                    own = int(tk[i+1])
        blk = re.findall(r'(?m)^\t\t\t' + str(p) + r'\s*=\s*\{[^}]*\}', tt)
        o.append(f'      该省在本州的 VP={own}, 省级建筑块={blk}')
o.append('')
for target in (484, 435, 500):
    f, plist, tt = sinfo[target]
    ow = re.search(r'owner\s*=\s*(\w+)', tt)
    o.append(f'  目标州{target} ({f}, owner={ow.group(1) if ow else "?"}): 现有 {len(plist)} 省: {plist}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

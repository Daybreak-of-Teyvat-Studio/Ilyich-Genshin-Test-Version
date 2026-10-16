# -*- coding: utf-8 -*-
import os, io, re, sys
sys.stdout.reconfigure(encoding='utf-8')

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
OUT = os.path.join(REPO, 'tools', 'vp_recon_out.txt')
o = []

ENTRIES = [
    (908, '风起地神像', 20), (3643, '鹰之门', 15), (352, '无相之雷', 20), (1306, '南风之狮的庙宇', 15),
    (1252, '西风之鹰的庙宇', 15), (3588, '忘却之峡', 15), (1535, '铭记之谷', 15), (473, '晨曦酒庄', 25),
    (3539, '苍风高地神像', 20), (733, '塞西莉亚苗圃', 15), (1334, '无相之风', 20), (288, '仲夏庭园', 15),
    (3383, '风龙废墟神像', 20), (3515, '急冻树', 20), (2273, '北风之狼的庙宇', 15), (3433, '西风大教堂', 25),
    (3456, '蒙德城风神像', 50), (1395, '蒙德大桥', 15), (292, '喷泉广场', 10), (3481, '西风骑士团总部', 50),
    (3441, '天使的馈赠', 15), (3485, '舒茨铁铺', 10), (1960, '阿卡狄亚遗迹', 15), (1930, '风车镇', 25),
    (3296, '风息山神像', 20), (1560, '山风的荆冕', 15), (919, '西风骑士团遗迹', 10), (3223, '疗养院旧址', 15),
    (1582, '守望者·堕天', 20), (2294, '宗室密藏之地', 10),
]
CAPITAL_ENTRY = 3481

# 1) 读全部州文件：省→州、州→(owner, VPs)
sd = os.path.join(G, 'history', 'states')
p2s = {}
state_info = {}
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    provs = [int(x) for x in m.group(1).split()] if m else []
    for p in provs:
        p2s[p] = sid
    ow = re.search(r'owner\s*=\s*(\w+)', t)
    vps = []
    for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        vps.append([int(x) for x in vm.group(1).split()])
    state_info[sid] = (ow.group(1) if ow else None, provs, vps, t)

o.append('=== 状态文件扫描 ===')
o.append(f'州数 {len(state_info)}, 省覆盖 {len(p2s)}')

# 2) 逐条检查
o.append('')
o.append('=== 30 条逐项检查 ===')
missing = []
by_state = {}
for pid, name, val in ENTRIES:
    sid = p2s.get(pid)
    if sid is None:
        missing.append(pid)
        o.append(f'  ✗ p{pid} {name}: 不属于任何州！！')
        continue
    owner, provs, vps, _ = state_info[sid]
    exist = None
    for vp in vps:
        for i in range(0, len(vp) - 1, 2):
            if vp[i] == pid:
                exist = vp[i+1]
    by_state.setdefault(sid, []).append((pid, name, val, exist))
    tag = ' ⚠已有VP值=' + str(exist) if exist is not None else ''
    o.append(f'  ✓ p{pid} {name}({val}): 州{sid} owner={owner}{tag}')

o.append('')
o.append(f'不存在的省: {missing if missing else "无 ✓"}')
o.append('')
o.append('=== 按州归组（同州多条要写一行） ===')
for sid in sorted(by_state):
    owner = state_info[sid][0]
    items = by_state[sid]
    o.append(f'  州{sid} (owner={owner}): {[(p, v) for p, n, v, e in items]}  [现有VP={state_info[sid][2]}]')

# 3) 首都信息
o.append('')
o.append('=== 3481（首都标记） ===')
sid = p2s.get(3481)
if sid:
    owner = state_info[sid][0]
    o.append(f'  p3481 → 州{sid}, owner={owner}')
    import glob as g2
    cfs = g2.glob(os.path.join(G, 'history', 'countries', f'{owner} - *.txt'))
    o.append(f'  国文件: {[os.path.basename(x) for x in cfs]}')
    for cf in cfs:
        ct = io.open(cf, 'rb').read().decode('utf-8-sig', errors='replace')
        for l in ct.splitlines()[:15]:
            if 'capital' in l or 'owner' in l:
                o.append(f'    {l.strip()[:100]}')

# 4) 现有同省 VP / loc 键冲突检查
o.append('')
o.append('=== loc 现状（这 30 个键是否已存在） ===')
locfiles = ['localisation/simp_chinese/DOT_Victory_Points_l_simp_chinese.yml',
            'localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml']
all_loc = {}
for rel in locfiles:
    fp = os.path.join(G, rel.replace('/', os.sep))
    if os.path.exists(fp):
        tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        for l in tt.splitlines():
            mm = re.match(r'\s*(VICTORY_POINTS_\d+)\s*:', l)
            if mm:
                all_loc.setdefault(mm.group(1), []).append((rel, l.strip()[:80]))
dups = []
for pid, name, val in ENTRIES:
    k = f'VICTORY_POINTS_{pid}'
    if k in all_loc:
        dups.append((k, all_loc[k]))
o.append(f'  已有同键: {dups if dups else "无 ✓"}')
# 全 simp_chinese 扫这 30 个键
import glob
found = {}
for fp in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for pid, name, val in ENTRIES:
        k = f'VICTORY_POINTS_{pid}'
        if k + ':' in tt:
            found.setdefault(k, []).append(os.path.basename(fp))
o.append(f'  全 simp_chinese 目录里已存在这些键的: {found if found else "无 ✓"}')

# 5) 现有州文件里"多 VP"的写法样例（确认格式约定）
o.append('')
o.append('=== 现有含 2+ 组数字的 victory_points 写法样例 ===')
cnt = 0
for sid, (owner, provs, vps, t) in state_info.items():
    for vp in vps:
        if len(vp) > 2:
            for mm in re.finditer(r'victory_points\s*=\s*\{[^}]*\}', t):
                if len([int(x) for x in mm.group(0).split('{')[1].split('}')[0].split()]) > 2:
                    o.append(f'  州{sid}: {mm.group(0)[:90]!r}')
                    cnt += 1
                    break
            break
    if cnt >= 10:
        break
o.append(f'  （{cnt} 例）')

# 6) 目标州文件当前 victory_points 原文
o.append('')
o.append('=== 目标州的 victory_points 原文 ===')
for sid in sorted(by_state):
    t = state_info[sid][3]
    m = re.findall(r'victory_points\s*=\s*\{[^}]*\}', t)
    o.append(f'  州{sid}: {m if m else "（无）"}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')

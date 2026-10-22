# -*- coding: utf-8 -*-
"""写入 30 个州名；设置胜利点 3825 归离城墟（10 点）+ 本地化"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
LOC = os.path.join(G, 'localisation', 'simp_chinese')
SN = os.path.join(LOC, 'DOT_state_names_gamma_l_simp_chinese.yml')
VPF = os.path.join(LOC, 'DOT_Victory_Points_l_simp_chinese.yml')

NEW = {467: '北风领', 544: '荻花洲', 479: '石门', 495: '无妄坡', 485: '轻策庄',
       502: '轻策庄南', 553: '归离原北', 585: '归离原', 599: '渌华池', 658: '璃月港',
       634: '绯云坡', 650: '天衡山', 657: '丹砂崖', 678: '天工峡', 679: '琉璃峰',
       649: '地面矿区', 629: '伏鳌谷', 608: '采樵谷', 536: '下川', 582: '翠峦坡',
       573: '绝云间', 554: '庆云顶', 542: '奥藏山', 561: '华光林', 575: '珀牢山',
       589: '南天门', 593: '天遒谷', 655: '青墟浦', 640: '灵矩关', 617: '遁玉陵'}
VP_PID, VP_NAME, VP_VAL = 3825, '归离城墟', 10

bdir = os.path.join(ROOT, '.backups', 'namesvp_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)

# 州是否存在
sids = {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sids[int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))] = f
miss = [s for s in NEW if s not in sids]
assert not miss, f'州不存在: {miss}'

# --- ① 30 个州名 ---
cur = open(SN, encoding='utf-8-sig', errors='replace').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))
for s, nm in NEW.items():
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
print(f'① 州名：写入 {len(NEW)} 个，文件共 {len(names)} 条')

# --- ② 胜利点 3825 ---
p2s = {}
for sid, f in sids.items():
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    for p in re.findall(r'\d+', re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1)):
        p2s[int(p)] = sid
sid = p2s[VP_PID]
fp = os.path.join(ST, sids[sid])
shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
t = open(fp, encoding='utf-8-sig', newline='').read()
line = f'victory_points = {{ {VP_PID} {VP_VAL} }}'
if re.search(r'victory_points\s*=\s*\{[^}]*\}', t):
    t = re.sub(r'victory_points\s*=\s*\{[^}]*\}', line, t, count=1)
    how = '替换'
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
with open(fp, 'w', encoding='utf-8', newline='') as fh:
    fh.write(t)
print(f'② 胜利点：state {sid} 的 {line}（{how}）')

# VP 本地化
shutil.copy2(VPF, os.path.join(bdir, os.path.basename(VPF)))
vt = open(VPF, encoding='utf-8-sig', errors='replace').read()
if f'VICTORY_POINTS_{VP_PID}:' not in vt:
    add = f' VICTORY_POINTS_{VP_PID}:0 "{VP_NAME}"'
    open(VPF, 'wb').write((vt.rstrip('\r\n') + '\r\n' + add + '\r\n').encode('utf-8'))
    print(f'   本地化追加：{add.strip()}')
else:
    print('   本地化已存在')
raw = open(VPF, 'rb').read()
if raw[:3] != b'\xef\xbb\xbf':
    open(VPF, 'wb').write(b'\xef\xbb\xbf' + raw)
    print('   （已补 BOM）')

# --- 复验 ---
print()
txt = open(SN, encoding='utf-8-sig', errors='replace').read()
v = dict((int(m.group(1)), m.group(2)) for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', txt, re.M))
named = {k: x for k, x in v.items() if x != '*'}
print(f'具名州总数 {len(named)}')
rawn = open(SN, 'rb').read()
print(f'州名文件 BOM={rawn[:3] == b"\xef\xbb\xbf"} CRLF={rawn.count(bytes([13,10]))}')
rawv = open(VPF, 'rb').read()
print(f'VP 文件 BOM={rawv[:3] == b"\xef\xbb\xbf"}  条目 {sum(1 for l in rawv.decode("utf-8-sig").splitlines() if "VICTORY_POINTS_" in l)}')
t2 = open(fp, encoding='utf-8-sig', errors='replace').read()
m = re.search(r'victory_points\s*=\s*\{([^}]*)\}', t2)
print(f'state {sid} 的 VP 行: {m.group(0) if m else "（无）"}')
print(f'\n备份 {bdir}')

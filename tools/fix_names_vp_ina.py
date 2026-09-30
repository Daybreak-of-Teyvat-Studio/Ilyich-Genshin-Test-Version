# -*- coding: utf-8 -*-
"""命名 47 州 + VP 16 个（4 首都）"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
CD = os.path.join(G, 'history', 'countries')
LOC = os.path.join(G, 'localisation', 'simp_chinese')
SN = os.path.join(LOC, 'DOT_state_names_gamma_l_simp_chinese.yml')
VPF = os.path.join(LOC, 'DOT_Victory_Points_l_simp_chinese.yml')

NAMES = {456: '遗珑埠', 471: '暝垣山', 480: '宝玦口', 465: '灵濛山', 472: '翘英庄',
         477: '古树茶坡', 513: '药蝶谷', 527: '奥藏山北', 530: '悬练山', 519: '赤璋城垣',
         516: '赤望台', 493: '沉珑渊', 492: '伏仙洞', 497: '锦落庭',
         111: '刃连岛', 110: '稻妻城', 134: '花见坂', 107: '白狐之野', 808: '绀田村',
         824: '镇守之森', 791: '影向山', 109: '神里屋敷', 99: '离岛', 795: '荒海',
         839: '九条阵屋', 101: '绯木村', 852: '蛇骨矿洞', 854: '无想刃狭间',
         118: '藤兜砦', 135: '踏鞴砂北', 849: '踏鞴砂', 121: '无明砦', 119: '珊瑚宫',
         120: '水月池', 128: '曚云神社', 851: '望泷村', 102: '茂知岛', 133: '浅濑神社',
         129: '平海砦', 130: '越石村', 855: '天云峠', 132: '千来神祠', 859: '知比山',
         137: '逢岳之野', 860: '菅名山', 861: '惑饲滩', 858: '茂知祭场'}
VPS = [(4556, '天守阁', 25, True), (680, '蛇神之首', 15, False), (881, '御影炉心', 20, False),
       (1485, '绯木村', 15, False), (4698, '茂知之壳', 10, False), (4649, '浅濑神社', 25, True),
       (707, '越石村', 15, False), (4651, '清籁岛神像', 15, False), (1327, '清籁丸', 10, False),
       (2106, '平海洞', 5, False), (4640, '沉眠之庭', 15, False), (2363, '知比洞', 5, False),
       (2274, '笈名海滨', 15, False), (4614, '月浴之渊', 25, True), (4668, '鹤观祭坛', 25, True)]

bdir = os.path.join(ROOT, '.backups', 'names_vp_ina_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)

# 现状
s2p, s2o, raw = {}, {}, {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    s2o[sid] = mo.group(1) if mo else None
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
    raw[sid] = t
p2s = {p: s for s, ps in s2p.items() for p in ps}

# ① 命名
cur = open(SN, encoding='utf-8-sig', errors='replace').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
miss = [s for s in NAMES if s not in s2p]
assert not miss, f'州不存在: {miss}'
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))
for s, nm in NAMES.items():
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
print(f'① 州名写入 {len(NAMES)} 个（文件共 {len(names)} 条）')

# ② VP + capital
p2s2 = {p: s for s, ps in s2p.items() for p in ps}
touched = set()
for pid, nm, val, cap in VPS:
    sid = p2s2[pid]
    touched.add(sid)
    fp = os.path.join(ST, sids_f := f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = open(fp, encoding='utf-8-sig', newline='').read()
    line = f'victory_points = {{ {pid} {val} }}'
    if re.search(r'victory_points\s*=\s*\{([^}]*)\}', t):
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
    tag = s2o[sid]
    print(f'  省 {pid}「{nm}」{val}点 → state {sid}（{tag}）{how}' + (' +capital' if cap else ''))
    if cap:
        cf = next((f for f in os.listdir(CD) if f.upper().startswith(tag)), None)
        assert cf, f'{tag} 国家文件缺'
        fp2 = os.path.join(CD, cf)
        shutil.copy2(fp2, os.path.join(bdir, cf))
        ct = open(fp2, encoding='utf-8-sig', newline='').read()
        if re.search(r'(?m)^\s*capital\s*=', ct):
            ct2 = re.sub(r'(?m)^(\s*capital\s*=\s*)\d+', rf'\g<1>{sid}', ct, count=1)
        else:
            ct2 = ct.rstrip('\r\n') + f'\r\n\r\ncapital = {sid}\r\n'
        with open(fp2, 'w', encoding='utf-8', newline='') as fh:
            fh.write(ct2)
        print(f'      {tag} capital = {sid}')

# VP 本地化
shutil.copy2(VPF, os.path.join(bdir, os.path.basename(VPF)))
vt = open(VPF, encoding='utf-8-sig', errors='replace').read()
add = []
for pid, nm, val, cap in VPS:
    k = f'VICTORY_POINTS_{pid}:'
    if k not in vt:
        add.append(f' VICTORY_POINTS_{pid}:0 "{nm}"')
    elif nm not in vt:
        # key 在但名字不同 → 替换该行
        vt = re.sub(rf'^(\s*VICTORY_POINTS_{pid}:0\s*)"[^"]*"', rf'\g<1>"{nm}"', vt, flags=re.M)
if add:
    vt = vt.rstrip('\r\n') + '\r\n' + '\r\n'.join(add) + '\r\n'
open(VPF, 'wb').write(b'\xef\xbb\xbf' + vt.encode('utf-8'))
rawv = open(VPF, 'rb').read()
print(f'VP 本地化：新增 {len(add)} 条，BOM={rawv[:3] == b"\xef\xbb\xbf"}')
rawn = open(SN, 'rb').read()
print(f'州名文件 BOM={rawn[:3] == b"\xef\xbb\xbf"} CRLF={rawn.count(bytes([13,10]))}')
print(f'\n备份 {bdir}')

# -*- coding: utf-8 -*-
"""① 转省 4 组 ② 3 个省级 VP ③ 13 个州名 ④ 合并 3 组记下不执行"""
import os, re, sys, subprocess, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VPF = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

# ① 转省
print('=== ① 转省 ===')
r = subprocess.run([sys.executable, TOOL, "336,1812+578.3859+600.340,1112+562.675,1611+579"],
                   capture_output=True, text=True, encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '转省 [', '省 ', '已写入', '备份', '同步', '校验', '!!', '跳过')):
        print('  ', l.strip()[:130])

# ② 省级 VP
VPS = [(4005, '阿佩普的行宫花园', 20), (1887, '居尔城墟·赤王神殿', 25), (701, '沙下灵囿', 15)]
print('\n=== ② 省级 VP ===')
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
        line = f'\t\tvictory_points = {{ {pid} {val} }}'
        t = t[:ls] + line + '\r\n' + t[ls:]
        how = '插入'
    open(fp, 'w', encoding='utf-8', newline='').write(t)
    print(f'  省 {pid}「{nm}」{val} → state {sid}（{how}）')
    vt = open(VPF, encoding='utf-8-sig', newline='').read()
    if f'VICTORY_POINTS_{pid}:' not in vt:
        nm_line = f' VICTORY_POINTS_{pid}:0 "{nm}"'
        open(VPF, 'wb').write((vt.rstrip('\r\n') + '\r\n' + nm_line + '\r\n').encode('utf-8'))

# ③ 州名
NAMES = {537: '精石铜城', 543: '聚香海岸', 571: '逾渊地墟', 592: '阻勒隘', 578: '荼泥黑渊',
         600: '铁穆山', 581: '甘露池', 545: '净觉湖', 562: '锋刃林泽', 531: '跋松顶',
         525: '遗忘之路', 703: '遗迹巨像', 579: '永世叹息之门'}
print('\n=== ③ 州名 ===')
miss = [s for s in NAMES if s not in p2s]
assert not miss, f'州不存在: {miss}'
bdir = os.path.join(ROOT, '.backups', 'names_sumer2_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))
cur = open(SN, encoding='utf-8-sig', newline='').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
for s, nm in NAMES.items():
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
raw = open(SN, 'rb').read()
print(f'  写入 {len(NAMES)} 个  BOM={raw[:3] == b"\xef\xbb\xbf"}  条数={len(names)}')
print(f'  备份 {bdir}')
print('\n=== ④ 合并 543+586=543、71+600=600、525+528=525：记下暂不执行 ===')

# -*- coding: utf-8 -*-
"""① 合并 21→72 ② 命名 6 州 ③ VP 42 条（同省聚合、覆盖规则）④ 核验"""
import os, re, sys, shutil, datetime, subprocess, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
VPF = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

# ① 合并 21 → 72（21 全省并入 72，21 清空）
print('=== ① 合并 21 → 72 ===')
s2p = {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
probs = s2p[21]
cmd = ','.join(map(str, probs)) + '+72'
print(f'  21 的 {len(probs)} 省 → 72')
r = subprocess.run([sys.executable, TOOL, cmd], capture_output=True, text=True,
                   encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '已写入', '备份', '同步', '校验', '!!')):
        print('  ', l.strip()[:130])

# ② 命名 6 州
NAMES = {441: '克莱门汀线', 386: '零落丘墟', 375: '学术会堂', 52: '玛丽安纪念公园',
         377: '德吕阿松林', 403: '欧蒂克莱尔'}
SN_bak = os.path.join(ROOT, '.backups', 'names_fon2_' +
                      datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(SN_bak, exist_ok=True)
shutil.copy2(SN, os.path.join(SN_bak, os.path.basename(SN)))
cur = open(SN, encoding='utf-8-sig', newline='').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
for s, nm in NAMES.items():
    print(f'  state {s}: 「{names.get(s)}」→「{nm}」')
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
print(f'② 命名 {len(NAMES)} 个写入')

# ③ VP 42 条（同省聚合；同 key 覆盖=后者生效）
VPS = [(866, '零落丘墟', 15), (3178, '黎翡区神像', 20), (3219, '回旋长廊', 5),
       (1065, '深潮的余响', 15), (1642, '神秘洞', 5), (1541, '棘球洞', 5),
       (1053, '桔桔薄饼站', 5), (3134, '布拉维的锻压工坊', 5), (927, '黎翡区神像', 20),
       (3155, '学术会堂', 10), (3188, '枫丹科学院驻外资质审核办公室', 10),
       (401, '实验性场力发生装置', 10), (1533, '资料院', 10), (2434, '行政院', 10),
       (3179, '猛烈纯洁小屋', 5), (3084, '奎瑟尔的发条工坊', 10),
       (3121, '科学院宿舍', 10), (1022, '果果软糖站', 10),
       (927, '动能工程研究院区神像', 20), (154, '博絮埃研究所', 10),
       (3183, '布拉维的藏书室', 10), (3096, '水文数据中枢处理站', 10),
       (3110, '发条应用研究院', 10), (3324, '黎翡区神像', 20), (3375, '白淞镇', 20),
       (2413, '荒野的洞窟', 10), (1636, '朽废的集所', 15),
       (1665, '铁甲熔火帝皇御座', 20), (1489, '晶山洞', 5), (3428, '炽热的洞窟', 10),
       (3655, '诺思托伊区神像', 20), (503, '褪色古堡', 15), (3635, '褪色的剧场', 20),
       (3557, '海露港', 20), (3306, '柔灯港', 20), (1381, '水与土之眼', 10),
       (1984, '【锈舵】', 10), (1069, '地下洞窟', 10), (2292, '湖东水道', 5),
       (1264, '伊黎耶之根', 10)]

# 读取（合并后的）省归属
p2s = {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        for q in re.findall(r'\d+', re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1)):
            p2s[int(q)] = sid

# 同省聚合（保持用户顺序；同省同后 key 覆盖）
per_state = collections.OrderedDict()
vp_names = collections.OrderedDict()
seen_pid = {}
for pid, nm, val in VPS:
    sid = p2s[pid]
    if pid in seen_pid:
        print(f'  ⚠ 省 {pid} 重复（前「{seen_pid[pid]}」后「{nm}」）→ 按顺序后者覆盖')
    seen_pid[pid] = nm
    per_state.setdefault(sid, collections.OrderedDict())[pid] = (nm, val)
    vp_names[pid] = nm

print('\n=== ③ VP 写入 ===')
shutil.copy2(VPF, os.path.join(SN_bak, os.path.basename(VPF)))
for sid, vps in sorted(per_state.items()):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(SN_bak, os.path.basename(fp)))
    t = open(fp, encoding='utf-8-sig', newline='').read()
    pairs = [(p, v[1]) for p, v in vps.items()]
    line = 'victory_points = { ' + ' '.join(f'{a} {b}' for a, b in pairs) + ' }'
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
    open(fp, 'w', encoding='utf-8', newline='').write(t)
    provs_txt = ', '.join(f'{p}({v[1]})' for p, v in vps.items())
    print(f'  state {sid}: {line[:80]}…（{how}，{len(vps)} 个）')

# VP 本地化
vt = open(VPF, encoding='utf-8-sig', newline='').read()
changed = 0
for pid, (nm, val) in vp_names.items():
    k = f'VICTORY_POINTS_{pid}:'
    pat = rf'^(\s*{re.escape(k)}0\s*)"[^"]*"'
    m = re.search(pat, vt, re.M)
    if m:
        if m.group(2) != nm:
            vt = re.sub(pat, rf'\g<1>"{nm}"', vt, count=1, flags=re.M)
            changed += 1
    else:
        vt = vt.rstrip('\r\n') + '\r\n' + f' VICTORY_POINTS_{pid}:0 "{nm}"' + '\r\n'
        changed += 1
open(VPF, 'wb').write(b'\xef\xbb\xbf' + vt.encode('utf-8'))
print(f'VP 本地化: {changed} 条新增/更新')

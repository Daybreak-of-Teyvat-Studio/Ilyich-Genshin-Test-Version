# -*- coding: utf-8 -*-
"""fix_natlan_batch.py —— 按用户原始指令修复纳塔批次的州名与 VP（字节级 BOM/CRLF 保持）

州名错挂修复（上轮会话把州号当省号解析）：
  · 恢复被覆盖的错号原值（3 个真名 + 8 个 *）
  · s720「柴薪之丘」保留（用户写的 1379 是省号，p1379∈s720，属正确落实）
  · 11 个名字写入指令州号
VP 修复（错位配对 + 多余写入）：
  · 删值：s735{389} s707{4154} s810{4484} s781{4356}
  · 加值：s747{2149:25} s722{1482:25} s782{4338:10}
  · VP 本地化：删 389/4154/4484/4356，加 2149烟谜主/1482花羽会/4338燃素开采研究所
"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
LOC = os.path.join(MOD, 'localisation', 'simp_chinese')
NAMES_F = os.path.join(LOC, 'DOT_state_names_gamma_l_simp_chinese.yml')
VP_F = os.path.join(LOC, 'DOT_Victory_Points_l_simp_chinese.yml')

# 错号 → 恢复原值（来自 names_natlan_20261003_224721 批次前备份）
RESTORE = {28: '*', 110: '稻妻城', 214: '*', 274: '*', 343: '*', 410: '*',
           423: '*', 595: '无郁稠林北', 613: '*', 645: '【三运河之地】', 742: '*'}
# 指令州号 → 名字
APPLY = {782: '燃素开采研究所', 814: '窃火者密岛', 106: '玉裙之丘', 828: '溶水域',
         747: '烟谜主', 766: '彩石顶', 105: '浮土静界', 781: '悬木人',
         643: '圣火竞技场', 810: '流泉之众', 767: '祖遗庙宇'}
# 州号 → 删 VP 值的省
VP_DEL = {735: [389], 707: [4154], 810: [4484], 781: [4356]}
# 州号 → 追加 (省, 值)
VP_ADD = {747: [(2149, 25)], 722: [(1482, 25)], 782: [(4338, 10)]}
# VP 本地化
VPLOC_DEL = [389, 4154, 4484, 4356]
VPLOC_ADD = [(2149, '烟谜主'), (1482, '花羽会'), (4338, '燃素开采研究所')]


def load(p):
    raw = open(p, 'rb').read()
    return raw, raw.decode('utf-8-sig')


def save(p, text, has_bom):
    data = text.encode('utf-8')
    open(p, 'wb').write((b'\xef\xbb\xbf' + data) if has_bom else data)


stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'natlan_fix_{stamp}')
os.makedirs(BD, exist_ok=True)
print(f'备份: {BD}')

# ---------- 1. 州名本地化 ----------
raw, t = load(NAMES_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
lines = re.split(r'(\r\n|\n)', t)  # 保留换行符本身的切分
nl = '\r\n' if '\r\n' in t else '\n'
out, changed = [], 0
for l in re.split(r'\r?\n', t):
    m = re.match(r'^(\s*DOT_STATE_(\d+):)\d*(\s*)"([^"]*)"', l)
    if m:
        sid = int(m.group(2))
        if sid in RESTORE and m.group(4) != RESTORE[sid]:
            l = f'{m.group(1)}:0{m.group(3)}"{RESTORE[sid]}"'
            changed += 1
        elif sid in APPLY and m.group(4) == '*':
            l = f'{m.group(1)}:0{m.group(3)}"{APPLY[sid]}"'
            changed += 1
        elif sid in APPLY and m.group(4) != APPLY[sid]:
            print(f'  !! s{sid} 现值「{m.group(4)}」≠ 占位，不覆盖，人工确认')
    out.append(l)
save(NAMES_F, nl.join(out), has_bom)
print(f'州名本地化: 改 {changed} 行（预期 22 = 恢复11 + 写入11）')

# ---------- 2. state 文件 VP 增删 ----------
def find_history_close(t):
    """history = { 的平衡闭合 } 在 t 中的下标"""
    m = re.search(r'\bhistory\s*=\s*\{', t)
    depth, i = 0, m.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError('history 块未闭合')


for sid, plist in VP_DEL.items():
    f = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(f, BD)
    raw, t = load(f)
    for pid in plist:
        pat = re.compile(r'([ \t]*)victory_points\s*=\s*\{\s*' + str(pid) +
                         r'\s+\d+\s*\}[ \t]*\r?\n?')
        t2, n = pat.subn('', t)
        # 删完可能留下空行 + 孤立 tab 残迹，清掉行内只剩空白的 victory_points 空洞
        t = t2
        print(f'  s{sid}: 删 p{pid} VP 条目 ×{n}')
    save(f, t, raw[:3] == b'\xef\xbb\xbf')

for sid, adds in VP_ADD.items():
    f = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(f, BD)
    raw, t = load(f)
    close = find_history_close(t)
    # 找 history 闭合行的行首缩进（一般是 \t}）
    ins = ''.join(f'\t\tvictory_points = {{ {pid} {val} }}{nl}' for pid, val in adds)
    # 插到闭合 } 所在行之前
    ls = t.rfind(nl, 0, close) + 1       # 闭合行行首
    head = t[:ls]
    if not head.endswith(nl):
        head += nl
    t = head + ins + t[ls:]
    save(f, t, raw[:3] == b'\xef\xbb\xbf')
    print(f'  s{sid}: 加 VP ' + ', '.join(f'p{pid}={v}' for pid, v in adds))

# ---------- 3. VP 本地化 ----------
raw, t = load(VP_F)
has_bom = raw[:3] == b'\xef\xbb\xbf'
nl = '\r\n' if '\r\n' in t else '\n'
lines = t.split(nl)
out, deleted = [], 0
for l in lines:
    m = re.match(r'^\s*VICTORY_POINTS_(\d+):', l)
    if m and int(m.group(1)) in VPLOC_DEL:
        deleted += 1
        continue
    out.append(l)
added = 0
existing = {int(m.group(1)) for m in
            (re.match(r'^\s*VICTORY_POINTS_(\d+):', l) for l in out) if m}
for pid, nm in VPLOC_ADD:
    if pid in existing:
        print(f'  !! VICTORY_POINTS_{pid} 已存在，不重复加')
        continue
    out.append(f' VICTORY_POINTS_{pid}:0 "{nm}"')
    added += 1
save(VP_F, nl.join(out), has_bom)
print(f'VP 本地化: 删 {deleted} 行，加 {added} 行')
print('完成。')

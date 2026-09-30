# -*- coding: utf-8 -*-
"""
更正州名本地化：
  · 清回我上次误命的 15 个州（181,184,222,227,265,349,510,530,606,645,702,724,743,778,839）→ "*"
  · 按 STATE 号写正确名（451,464,474,484,424,454,435,422,412,437,505,64,483,500）
  · 1466 不存在 → 暂不处理，等用户确认
"""
import os, re, sys, shutil, datetime, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
LOC = os.path.join(G, 'localisation', 'simp_chinese')
SN = os.path.join(LOC, 'DOT_state_names_gamma_l_simp_chinese.yml')

WRONG = [181, 184, 222, 227, 265, 349, 510, 530, 606, 645, 702, 724, 743, 778, 839]
CORRECT = {451: '低语森林', 464: '摘星崖', 474: '千风神殿', 484: '风起地', 424: '望风角',
           454: '星落湖', 435: '鹰翔海滩', 422: '望风山地', 412: '风车镇', 437: '明冠峡',
           505: '誓言岬', 64: '马斯克礁', 483: '清泉镇', 500: '晨曦酒庄'}

# 读现有全部名字
cur = open(SN, encoding='utf-8-sig', errors='replace').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)

# 校验州是否存在
sids = set()
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sids.add(int(re.search(r'\bid\s*=\s*(\d+)', t).group(1)))

print('=== 更正内容 ===')
for s in WRONG:
    if s in names and names[s] != '*':
        print(f'  清回「*」: state {s}（原误名「{names[s]}」）')
        names[s] = '*'
for s, nm in sorted(CORRECT.items()):
    assert s in sids, f'state {s} 不存在'
    print(f'  命名为「{nm}」: state {s}（原「{names.get(s)}」）')
    names[s] = nm

# 备份并写
bdir = os.path.join(ROOT, '.backups', 'names_fix_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))

lines = ['l_simp_chinese:']
for s in sorted(names):
    lines.append(f' DOT_STATE_{s}:0 "{names[s]}"')
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
raw = open(SN, 'rb').read()
print(f'\n已写入 {SN}')
print(f'  BOM={raw[:3] == b"\xef\xbb\xbf"}  CRLF={raw.count(bytes([13,10]))}/LF={raw.count(bytes([10]))}  条数={len(names)}')
print(f'  备份 {bdir}')

# 复验
txt = open(SN, encoding='utf-8-sig', errors='replace').read()
v = dict((int(m.group(1)), m.group(2)) for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', txt, re.M))
named = {k: x for k, x in v.items() if x != '*'}
print(f'\n=== 现在具名州 {len(named)} 个 ===')
for k in sorted(named):
    mo = None
    p = os.path.join(ST, f'{k}-State_{k}.txt')
    if os.path.exists(p):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    print(f'  state {k:5d}（{mo.group(1) if mo else "海州"}）: 「{named[k]}」')

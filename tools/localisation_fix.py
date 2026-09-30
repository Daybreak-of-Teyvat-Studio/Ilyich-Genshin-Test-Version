# -*- coding: utf-8 -*-
"""
修复本地化（甲信越等原版名字混入）：
  1. state 文件 name="STATE_<id>" → name="DOT_STATE_<id>"（避开原版 STATE_<id> 撞名）
  2. 重写州名本地化：BOM + 全 CRLF + DOT_STATE_<id> 前缀
  3. 补回 VP 本地化的 BOM（上次 vp_371.py 写丢了）
先备份，再改，最后复验。
"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
LOC = os.path.join(G, 'localisation', 'simp_chinese')
SN = os.path.join(LOC, 'DOT_state_names_gamma_l_simp_chinese.yml')
VP = os.path.join(LOC, 'DOT_Victory_Points_l_simp_chinese.yml')

# ---- 0. 读出当前命名（15 个中文名，其余为 *）----
cur = open(SN, encoding='utf-8-sig', errors='replace').read()
names = {}
for m in re.finditer(r'^\s*STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
named = {k: v for k, v in names.items() if v != '*'}
print(f'现有 {len(names)} 条州名，其中具名 {len(named)} 个:')
for k in sorted(named):
    print(f'    {k} = {named[k]}')

# 确保覆盖所有 state 文件（含新增海州）
sids = []
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sids.append(int(re.search(r'\bid\s*=\s*(\d+)', t).group(1)))
sids = sorted(set(sids))
print(f'\nstate 文件 {len(sids)} 个（{min(sids)}-{max(sids)}）')

bdir = os.path.join(ROOT, '.backups', 'locfix_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)

# ---- 1. state 文件 name key 加前缀 ----
n = 0
for sid in sids:
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    if not os.path.exists(fp):
        continue
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = open(fp, encoding='utf-8-sig', newline='').read()
    t2 = re.sub(r'(\bname\s*=\s*)"STATE_(\d+)"', r'\1"DOT_STATE_\2"', t, count=1)
    if t2 != t:
        with open(fp, 'w', encoding='utf-8', newline='') as fh:
            fh.write(t2)
        n += 1
print(f'\n1) state 文件 name 加前缀：{n} 个')

# ---- 2. 重写州名本地化（BOM + CRLF + 新前缀）----
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))
lines = ['l_simp_chinese:']
for sid in sids:
    lines.append(f' DOT_STATE_{sid}:0 "{names.get(sid, "*")}"')
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
raw = open(SN, 'rb').read()
print(f'2) 州名本地化重写：{len(lines)-1} 条  BOM={raw[:3] == b"\xef\xbb\xbf"}  '
      f'CRLF={raw.count(bytes([13,10]))}/LF={raw.count(bytes([10]))}')

# ---- 3. VP 本地化补 BOM ----
rawv = open(VP, 'rb').read()
if rawv[:3] != b'\xef\xbb\xbf':
    shutil.copy2(VP, os.path.join(bdir, os.path.basename(VP)))
    t = rawv.decode('utf-8-sig')
    t = '\r\n'.join(l.rstrip('\r') for l in t.split('\n'))
    open(VP, 'wb').write(b'\xef\xbb\xbf' + t.encode('utf-8'))
    rawv = open(VP, 'rb').read()
    print(f'3) VP 本地化补 BOM: BOM={rawv[:3] == b"\xef\xbb\xbf"}  '
          f'CRLF={rawv.count(bytes([13,10]))}/LF={rawv.count(bytes([10]))}')
else:
    print('3) VP 本地化已有 BOM')

# ---- 4. 复验 ----
print('\n4) 复验')
bad = []
for sid in sids:
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    if not os.path.exists(fp):
        continue
    t = open(fp, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'\bname\s*=\s*"([^"]*)"', t)
    if not m or m.group(1) != f'DOT_STATE_{sid}':
        bad.append((sid, m.group(1) if m else None))
print(f'   state 文件 name 不正确: {len(bad)} {bad[:5]}')
txt = open(SN, encoding='utf-8-sig', errors='replace').read()
keys = set(re.findall(r'^\s*(DOT_STATE_\d+):', txt, re.M))
print(f'   本地化 key 数: {len(keys)}（应 {len(sids)}）')
missing = [s for s in sids if f'DOT_STATE_{s}' not in keys]
print(f'   缺 key 的州: {len(missing)} {missing[:5]}')
print(f'   具名条目保留: {sum(1 for l in txt.splitlines() if "DOT_STATE_" in l and l.rstrip().endswith('"*"') == False)}')

# ---- 5. 全 mod 其他文件是否还引用 STATE_<id> ----
hits = []
for root, dirs, files in os.walk(G):
    if 'localisation' in root:
        continue
    for f in files:
        if f.endswith(('.txt', '.yml')):
            p = os.path.join(root, f)
            try:
                t = open(p, encoding='utf-8-sig', errors='replace').read()
            except Exception:
                continue
            if re.search(r'\bSTATE_\d+\b', t):
                hits.append(os.path.relpath(p, G))
print(f'\n5) 其他文件仍引用 STATE_<id> 的: {len(hits)} {hits[:8]}')
print(f'\n备份: {bdir}')

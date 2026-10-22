# -*- coding: utf-8 -*-
"""fix_chained_merge.py —— 收尾三件事
1) 567 的 5 个省补回 s550（连锁合并覆盖 bug 的修复）
2) s759 → s750（消除尾部空洞，1-750 全连号）：id/name/文件/本地化/首都/buildings列/引用 全联动
3) 打印 759 内容概要供核对"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
NAMES_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
BP = os.path.join(MOD, 'map', 'buildings.txt')

# ---------- 1. 567 的 5 省补回 s550 ----------
f550 = os.path.join(ST, '550-State_550.txt')
t = open(f550, encoding='utf-8-sig', errors='replace').read()
pa = re.search(r'(provinces\s*=\s*\{)([^}]*)(\})', t)
provs = pa.group(2).split()
add = [p for p in ('478', '1204', '1500', '1869', '3766') if p not in provs]
provs += add
t = t[:pa.start()] + pa.group(1) + '\r\n\t\t' + ' '.join(provs) + '\r\n\t' + pa.group(3) + t[pa.end():]
open(f550, 'wb').write(t.encode('utf-8'))
print(f's550 补回 {len(add)} 省: {add}')

# ---------- 2. s759 → s750 ----------
f759 = os.path.join(ST, '759-State_759.txt')
t = open(f759, encoding='utf-8-sig', errors='replace').read()
om = re.search(r'\bowner\s*=\s*(\w+)', t)
print(f's759 内容: owner={om.group(1) if om else "海"}，省 {re.search(r"provinces = .([^}]*)", t).group(1).split()}')
t2 = re.sub(r'(\bid\s*=\s*)\d+', r'\g<1>750', t, count=1)
t2 = re.sub(r'(\bname\s*=\s*")DOT_STATE_\d+(")', r'\g<1>DOT_STATE_750\g<2>', t2, count=1)
open(os.path.join(ST, '750-State_750.txt'), 'wb').write(t2.encode('utf-8'))
os.remove(f759)
# 本地化
raw = open(NAMES_F, 'rb').read()
has_bom = raw[:3] == b'\xef\xbb\xbf'
t = raw.decode('utf-8-sig')
t2, n = re.subn(r'(DOT_STATE_759:)', r'\g<1>0', t)
t2 = t2.replace('DOT_STATE_759:0', 'DOT_STATE_750:0')
open(NAMES_F, 'wb').write(((b'\xef\xbb\xbf' if has_bom else b'') + t2.encode('utf-8')))
print(f'本地化 759→750: {n} 行改写')
# 首都
for p in glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    t2 = re.sub(r'(?m)^(\s*capital\s*=\s*)759\s*$', r'\g<1>750', t)
    if t2 != t:
        open(p, 'wb').write(t2.encode('utf-8'))
        print(f'首都联动: {os.path.basename(p)}')
# buildings 列
raw = open(BP, 'rb').read()
nl = '\r\n' if b'\r\n' in raw else '\n'
lines = raw.decode('utf-8-sig').split(nl)
nb = 0
for i, l in enumerate(lines):
    f7 = l.split(';')
    if len(f7) == 7 and f7[0] == '759':
        f7[0] = '750'
        lines[i] = ';'.join(f7)
        nb += 1
open(BP, 'wb').write(nl.join(lines).encode('utf-8'))
print(f'buildings 列 759→750: {nb} 条')
# 引用（common/events/countries 单值 token）
TOKEN = re.compile(r'\b(owns_state|controls_state|has_full_control_of|transfer_state|state)\s*=\s*759\b')
n_r = 0
for root, dirs, files in os.walk(MOD):
    dirs[:] = [d for d in dirs if d not in ('.backups', '.git') and '备份' not in d]
    for f in files:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(root, f)
        rr = os.path.relpath(p, MOD).replace('\\', '/')
        if rr.startswith('history/states') or rr == 'map/buildings.txt':
            continue
        raw = open(p, 'rb').read()
        t = raw.decode('utf-8-sig', errors='replace')
        t2, n = TOKEN.subn(lambda m: m.group(1) + ' = 750', t)
        if n:
            data = t2.encode('utf-8')
            open(p, 'wb').write((b'\xef\xbb\xbf' + data) if raw[:3] == b'\xef\xbb\xbf' else data)
            n_r += n
print(f'引用 759→750: {n_r} 处')

# ---------- 3. 终验 ----------
fs = glob.glob(os.path.join(ST, '*.txt'))
ids = sorted(int(re.match(r'(\d+)-', os.path.basename(f)).group(1))
             for f in fs if re.match(r'\d+-', os.path.basename(f)))
holes = sorted(set(range(ids[0], ids[-1] + 1)) - set(ids))
sne = sum(1 for f in fs if 'owner = SNE' in open(f, encoding='utf-8-sig', errors='replace').read())
print(f'终验: 文件 {len(fs)}，范围 {ids[0]}-{ids[-1]}，缺号 {holes or "无"}，SNE {sne}')

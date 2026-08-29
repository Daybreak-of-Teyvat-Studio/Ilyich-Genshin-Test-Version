# -*- coding: utf-8 -*-
import os, re
from collections import Counter, defaultdict
import openpyxl

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
GAMMA = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
XLSX = os.path.join(ROOT, '地块迁移_Gamma州映射_几何.xlsx')

# Gamma -> Beta mapping
wb = openpyxl.load_workbook(XLSX, read_only=True)
ws = wb['Gamma州映射']
rows = list(ws.iter_rows(values_only=True))
gamma_to_beta = {int(r[0]): int(r[3]) for r in rows[1:]}

# which Beta states are matched (used) vs orphaned
used = set(gamma_to_beta.values())
print('matched Beta states:', len(used), 'of 740')

# parse beta manpower + resources
def beta_stats(states_dir):
    out = {}
    for fn in os.listdir(states_dir):
        if not fn.endswith('.txt'):
            continue
        t = open(os.path.join(states_dir, fn), encoding='utf-8').read()
        m = re.search(r'\bid\s*=\s*(\d+)', t)
        if not m:
            continue
        bid = int(m.group(1))
        mm = re.search(r'manpower\s*=\s*(\d+)', t)
        man = int(mm.group(1)) if mm else 0
        res = {}
        rb = re.search(r'resources\s*=\s*\{(.*?)\}', t, re.S)
        if rb:
            for k, v in re.findall(r'(\w+)\s*=\s*([\d.]+)', rb.group(1)):
                res[k] = float(v)
        out[bid] = (man, res)
    return out

bs = beta_stats(os.path.join(BETA, 'history', 'states'))
matched_man = sum(bs[b][0] for b in used)
total_man = sum(bs[b][0] for b in bs)
print('matched manpower %.0f / total %.0f = %.2f' % (matched_man, total_man, matched_man / total_man))

# gamma original names (from backup)
bk = os.path.join(ROOT, '.backups', 'gamma_states_20260828_165343')
names = Counter()
for fn in os.listdir(bk):
    if not fn.endswith('.txt'):
        continue
    t = open(os.path.join(bk, fn), encoding='utf-8').read()
    m = re.search(r'name\s*=\s*"([^"]*)"', t)
    if m:
        names[m.group(1)] += 1
print('Gamma original unique names:', len(names))
print('top Gamma original names:', names.most_common(10))

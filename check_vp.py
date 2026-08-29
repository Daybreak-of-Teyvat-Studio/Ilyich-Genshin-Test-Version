# -*- coding: utf-8 -*-
import os, re
from collections import Counter

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
gs = os.path.join(G, 'history', 'states')

# count victory points in state files, and check membership
vp_total = 0
vp_orphan = 0
for fn in os.listdir(gs):
    if not fn.endswith('.txt'):
        continue
    t = open(os.path.join(gs, fn), encoding='utf-8').read()
    provs = set(re.findall(r'\d+', (re.search(r'provinces = \{(.*?)\}', t, re.S) or re.search(r'', t)).group(1))) if re.search(r'provinces = \{(.*?)\}', t, re.S) else set()
    for pid in re.findall(r'victory_points = \{ (\d+)', t):
        vp_total += 1
        if pid not in provs:
            vp_orphan += 1
print('gamma victory_points total:', vp_total, 'orphan (not in provinces):', vp_orphan)

# check remapped VP localization file
vpfile = os.path.join(G, 'localisation', 'simp_chinese', 'victory_points_l_simp_chinese.yml')
t = open(vpfile, encoding='utf-8').read()
print('VP loc head:')
for line in t.splitlines()[1:6]:
    print('  ', line)

# check the 9 unmapped VP provinces - find them in Beta
B = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version'
# collect beta VP provinces
beta_vp = set()
for fn in os.listdir(os.path.join(B, 'history', 'states')):
    if not fn.endswith('.txt'):
        continue
    tt = open(os.path.join(B, 'history', 'states', fn), encoding='utf-8').read()
    beta_vp |= set(int(x) for x in re.findall(r'victory_points = \{ (\d+)', tt))

# gamma provinces (from gamma state files)
gamma_provs = set()
for fn in os.listdir(gs):
    if not fn.endswith('.txt'):
        continue
    tt = open(os.path.join(gs, fn), encoding='utf-8').read()
    m = re.search(r'provinces = \{(.*?)\}', tt, re.S)
    if m:
        gamma_provs |= set(int(x) for x in re.findall(r'\d+', m.group(1)))

print('beta VP provinces count:', len(beta_vp))
print('gamma land provinces (in states):', len(gamma_provs))

# new state-name localization file
nf = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Gamma_state_names_l_simp_chinese.yml')
if os.path.exists(nf):
    lines = open(nf, encoding='utf-8').read().splitlines()
    print('name loc file lines:', len(lines), 'sample:', lines[1:4])

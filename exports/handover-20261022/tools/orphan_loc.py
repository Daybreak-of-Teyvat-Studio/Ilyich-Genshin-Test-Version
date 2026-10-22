# -*- coding: utf-8 -*-
import os, io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
OUT = os.path.join(REPO, 'tools', 'orphan_loc_out.txt')
o = []

fp = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
t = io.open(fp, 'rb').read().decode('utf-8-sig')
keys = ['DOT_STATE_62','DOT_STATE_63','DOT_STATE_65','DOT_STATE_66','DOT_STATE_67',
        'DOT_STATE_703','DOT_STATE_704','DOT_STATE_705','DOT_STATE_706',
        'DOT_STATE_89','DOT_STATE_90','DOT_STATE_94',
        'DOT_STATE_707','DOT_STATE_708','DOT_STATE_709','DOT_STATE_710','DOT_STATE_711','DOT_STATE_712']
o.append('===== DOT_state_names_gamma 里的相关键 =====')
for l in t.splitlines():
    for k in keys:
        if re.match(r'\s*' + k + r':', l):
            o.append('  ' + l.strip()[:110])
            break
# 也搜其他 loc 文件
import glob
for fp2 in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    if fp2 == fp:
        continue
    tt = io.open(fp2, 'rb').read().decode('utf-8-sig', errors='replace')
    for l in tt.splitlines():
        for k in keys:
            if re.match(r'\s*' + k + r':', l):
                o.append(f'  [{os.path.basename(fp2)}] ' + l.strip()[:110])
                break

# 20 个州的现名（从 loc）
o.append('')
o.append('===== 补号前 703-706 现在该显示的州（对照蒙古/须弥区州文件注释） =====')
sd = os.path.join(G, 'history', 'states')
for sid in (63, 65, 66, 67):
    tt = io.open(os.path.join(sd, f'{sid}-State_{sid}.txt'), 'rb').read().decode('utf-8-sig')
    for l in tt.splitlines()[:4]:
        if 'name=' in l:
            o.append(f'  {sid}: {l.strip()[:90]}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

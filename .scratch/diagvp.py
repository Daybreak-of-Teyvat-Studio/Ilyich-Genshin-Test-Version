# -*- coding: utf-8 -*-
"""快速诊断：为什么 VP 标注图显示 VPxxxx 而不是中文名"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
BETA = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version'
VPF = os.path.join(BETA, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')

# ① VP 本地化文件是否存在
print('① VP 本地化文件:', os.path.exists(VPF))
if os.path.exists(VPF):
    raw = open(VPF, 'rb').read()
    print(f'   BOM={raw[:3] == b"\xef\xbb\xbf"}  字节={len(raw)}')
    t = raw.decode('utf-8-sig', errors='replace')
    keys = re.findall(r'VICTORY_POINTS_(\d+):', t)
    print(f'   key 数={len(keys)}  前 5: {keys[:5]}')

# ② Beta state 文件里的 VP 数据
ST = os.path.join(BETA, 'history', 'states')
vp_count = 0
vp_sample = []
for f in sorted(os.listdir(ST))[:10]:
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
        v = m.group(1).split()
        for i in range(0, len(v) - 1, 2):
            vp_count += 1
            if len(vp_sample) < 5:
                vp_sample.append((int(v[i]), int(v[i + 1]), f))
print(f'② Beta VP 数据: 总数 {vp_count}  样例 {vp_sample}')

# ③ beta_vp_map2.py 里 vp_names 的数据源
print('\n③ 脚本 VP 名数据源:')
print('   vp_file 变量指向:', VPF)
print('   = Beta 版目录下（不是 Gamma）')

# ④ 检查 tools/beta_vp_map2.py 里 vp_names 加载逻辑
p = r'tools/beta_vp_map2.py'
code = open(p, encoding='utf-8').read()
# 找 vp_names 填充的位置
for i, l in enumerate(code.split('\n')):
    if 'vp_names' in l and ('=' in l or 'read' in l or 'finditer' in l):
        print(f'   行{i+1}: {l.strip()[:100]}')

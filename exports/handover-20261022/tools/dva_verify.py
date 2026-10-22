# -*- coding: utf-8 -*-
"""dva_verify.py —— 核实 DVA 案例：beta 州名/VP、gamma 对应州、DVA_1936 单位、path 块"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# beta 中文 loc
bloc = {}
for p in glob.glob(os.path.join(B, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*([A-Za-z][\w ]*?):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        bloc.setdefault(m.group(1).strip(), m.group(2))

print('=== beta 风龙系州（60/76/79/82/64）的名字与 VP ===')
beta_vp = {}
for p in glob.glob(os.path.join(B, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        beta_vp[int(m.group(1))] = m.group(2)
for sid in (60, 76, 79, 82, 64):
    for f in glob.glob(os.path.join(B, 'history', 'states', '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        if int(re.search(r'\bid\s*=\s*(\d+)', t).group(1)) != sid:
            continue
        nm = re.search(r'name\s*=\s*"([^"]+)"', t)
        cn = bloc.get(nm.group(1), nm.group(1))
        provs = re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()
        vps = re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', t)
        print(f'  beta s{sid}「{cn}」({nm.group(1)}) 省{len(provs)}个')
        for pid, val in vps:
            print(f'      VP p{pid}「{beta_vp.get(int(pid), "?")}」{val}')

print()
print('=== gamma 风龙系州 ===')
gname = {}
for p in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s*"([^"]*)"',
                         open(p, encoding='utf-8-sig', errors='replace').read(), re.M):
        gname[int(m.group(1))] = m.group(2)
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    if om and om.group(1) == 'DVA':
        provs = re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()
        vps = re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', t)
        print(f'  gamma s{sid}「{gname.get(sid, "?")}」owner=DVA 省{provs}')
        print(f'      VP {vps}')
# 谁拥有 60/76 号州（gamma）
for f in glob.glob(os.path.join(G, 'history', 'states', '60-State_60.txt')) + \
         glob.glob(os.path.join(G, 'history', 'states', '76-State_76.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = re.search(r'\bid\s*=\s*(\d+)', t).group(1)
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    print(f'  gamma s{sid} 现 owner={om.group(1) if om else "海"}（提醒：不能沿用 beta 号）')

print()
print('=== DVA_1936.txt 全部 location ===')
t = open(os.path.join(G, 'history', 'units', 'DVA_1936.txt'), encoding='utf-8-sig', errors='replace').read()
for i, l in enumerate(t.splitlines(), 1):
    if 'location' in l or 'division_template' in l:
        print(f'  {i}: {l.strip()}')

print()
print('=== 全 mod 的 path = { } 块统计 ===')
import collections
cnt = collections.Counter()
for root, dirs, files in os.walk(G):
    dirs[:] = [d for d in dirs if d not in ('.backups', '.backup', '备份', '.git')]
    for f in files:
        if not f.endswith('.txt'):
            continue
        t = open(os.path.join(root, f), encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(r'path\s*=\s*\{([^}]*)\}', t):
            ids = [int(x) for x in m.group(1).split() if x.isdigit()]
            cnt[os.path.relpath(os.path.join(root, f), G)] += 1
for k, v in cnt.most_common(20):
    print(f'  {k}: {v} 个 path 块')

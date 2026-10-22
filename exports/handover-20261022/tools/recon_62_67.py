# -*- coding: utf-8 -*-
"""recon_62_67.py —— 州 62-67 画像 + 战略区结构（只读）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read().split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = c[4]
        except ValueError:
            pass

allloc = ''
for f in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(f, encoding='utf-8-sig', errors='replace').read()

print('=== 州 62-67 画像 ===')
for sid in (62, 63, 64, 65, 66, 67):
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{sid}*.txt'))
          if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    if not fs:
        print(f'  s{sid}: ★无文件')
        continue
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    ps = [int(x) for x in re.findall(r'\d+', m2.group(1))] if m2 else []
    cat = re.search(r'state_category\s*=\s*(\S+)', t)
    man = re.search(r'manpower\s*=\s*(\d+)', t)
    bld = re.findall(r'(?m)^\s*([a-z_]+)\s*=\s*(\d+)', t)
    vp = re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)', t)
    lm = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', allloc)
    kinds = set(gk.get(p) for p in ps)
    print(f'  s{sid}: loc={lm.group(1) if lm else "★无"} owner={m.group(1) if m else "-"} cat={cat.group(1) if cat else "-"} man={man.group(1) if man else "-"}')
    print(f'      省({len(ps)}): {ps[:15]} kind={kinds}')
    print(f'      建筑: {bld[:8]}  VP: {vp}')

print()
print('=== 战略区文件结构 ===')
sr = glob.glob(os.path.join(G, 'map', 'strategicregions', '*.txt'))
for f in sr:
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    regs = re.findall(r'strategic_region\s*=\s*\{[^}]*?id\s*=\s*(\d+)[^}]*?name\s*=\s*"([^"]*)"', t, re.S)
    nprov = len(re.findall(r'(?m)^\s*\d+\s*$', t))
    print(f'  {os.path.basename(f)}: {len(regs)} 个区域 {regs} 省枚举行≈{nprov}')
    print('  头 12 行:')
    for l in t.split('\n')[:12]:
        print('   ', l.rstrip()[:100])

print()
print('=== 战略区名字 loc ===')
for m in re.finditer(r'(?m)^\s*DOT_STRATEGICREGIONS[^\n]*', allloc):
    print('  ', m.group(0).strip()[:120])

print()
print('=== 62-67 的省份在全图什么位置（含坐标）===')
import struct
raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
W, H = struct.unpack('<ii', raw[18:26])
RB = W * 3
colors = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read().split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            colors[(int(c[1]), int(c[2]), int(c[3]))] = int(c[0])
        except ValueError:
            pass
# 找 62-67 各省首个像素坐标
want = set()
for sid in (62, 63, 64, 65, 66, 67):
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{sid}*.txt'))
          if re.match(rf'^{sid}(\(|-)', os.path.basename(f))]
    if fs:
        t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
        m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        if m2:
            want |= set(int(x) for x in re.findall(r'\d+', m2.group(1)))
found = {}
for z in range(0, H, 4):
    for x in range(0, W, 4):
        i = z * RB + x * 3
        p = colors.get((raw[i + 2], raw[i + 1], raw[i]))
        if p in want and p not in found:
            found[p] = (x, z)
for p in sorted(found):
    print(f'  省{p}: 首像素({found[p][0]},{found[p][1]})', end='  ')
print()

# -*- coding: utf-8 -*-
"""micro_reads.py —— ①x=4095/0 环绕交叉 ②INA 新增变体块全文"""
import os, re, sys, struct

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('【①】provinces.bmp x=4093..4095 与 x=0..2 并排（看环绕交叉）')
raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
W, H = struct.unpack('<ii', raw[18:26])
RB = W * 3
colors = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            colors[(int(c[1]), int(c[2]), int(c[3]))] = int(c[0])
        except ValueError:
            pass

def pid(x, z):
    i = off + z * RB + x * 3
    return colors.get((raw[i + 2], raw[i + 1], raw[i]))

for zz in (478, 479, 480, 481, 482, 1565, 1566, 1567, 1568, 1569):
    left = [pid(x, zz) for x in (0, 1, 2)]
    right = [pid(x, zz) for x in (4093, 4094, 4095)]
    print(f'  z={zz:<5} x0-2={left}  x4093-95={right}   环绕对: {left[0]}/{right[2]}')

print()
print('【②】INA - Inazuma.txt 新增的 5 个变体块全文')
p = os.path.join(G, 'history', 'countries', 'INA - Inazuma.txt')
t = open(p, encoding='utf-8-sig', errors='replace').read()
for m in re.finditer(r'create_equipment_variant\s*=\s*\{', t):
    depth, i = 0, m.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    blk = t[m.start():i + 1]
    if 'Sumeru_Class' in blk or 'Natlan_Class' in blk or 'Snezhnaya_Class' in blk or 'Fontaine_Class' in blk:
        print('  ---')
        for l in blk.split('\n'):
            print('   ', l.rstrip()[:120])
print()
print('【③】原版模板（同 hull 的第一个）对比 —— cruiser_2 的模板长啥样')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
import glob
found = 0
for f in glob.glob(os.path.join(V, 'history', 'countries', '*.txt')):
    t2 = open(f, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'create_equipment_variant\s*=\s*\{', t2):
        depth, i = 0, m.end() - 1
        while i < len(t2):
            if t2[i] == '{':
                depth += 1
            elif t2[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blk = t2[m.start():i + 1]
        if re.search(r'type\s*=\s*ship_hull_cruiser_2\b', blk):
            print(f'  [{os.path.basename(f)}] 第一个 cruiser_2 变体块:')
            for l in blk.split('\n')[:22]:
                print('   ', l.rstrip()[:120])
            found = 1
            break
    if found:
        break

# -*- coding: utf-8 -*-
"""修复 1/2：positions.txt 的 14 个落海州首府坐标。
做法：按字节读取，只替换这些省块里 position={...} 的 6 行数值，其余字节原样保留。
产物写到 .workbuddy/positions_fix14.txt（不直接覆盖 map/positions.txt）。"""
import struct, os, re, json, hashlib
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
MAP = os.path.join(MOD, 'map')
SRC = os.path.join(MAP, 'positions.txt')
OUT = os.path.join(ROOT, '.workbuddy', 'positions_fix14.txt')
BK = os.path.join(ROOT, '.workbuddy', 'backup_20260924_positions')
REP = os.path.join(ROOT, '.workbuddy', 'report_positions_fix14.txt')
os.makedirs(BK, exist_ok=True)

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

plan = json.load(open(os.path.join(ROOT, '.workbuddy', 'vp14_plan.json')))
plan = {int(k): v for k, v in plan.items()}
P(f'待修省 {len(plan)} 个: {sorted(plan)}')
P('')

data = open(SRC, 'rb').read()
P(f'原文件 {len(data):,} B  md5={hashlib.md5(data).hexdigest()}')
open(os.path.join(BK, 'positions.txt'), 'wb').write(data)
P(f'已备份 -> {os.path.join(BK, "positions.txt")}')
P('')

lines = data.split(b'\n')
P(f'行数 {len(lines):,}  （CRLF 行 {data.count(bytes([13,10])):,}）')

# 找到每个待修省的块，替换 position 段的 6 行
changed = {}
i = 0
while i < len(lines):
    core = lines[i].rstrip(b'\r')
    m = re.match(rb'^(\d+)=\{$', core)
    if m and int(m.group(1)) in plan:
        pid = int(m.group(1))
        tx, ty = plan[pid]
        # 找 position={
        j = i + 1
        while j < len(lines) and b'position' not in lines[j]:
            j += 1
        # position={ 之后 6 行数值
        k = j + 1
        old = []
        cnt = 0
        while k < len(lines) and cnt < 6:
            c2 = lines[k].rstrip(b'\r')
            if re.match(rb'^\s*[\d.]+\s+[\d.]+\s+[\d.]+\s*$', c2):
                old.append(c2.decode())
                tail = lines[k][len(c2):]
                indent = lines[k][:len(lines[k]) - len(lines[k].lstrip())]
                lines[k] = indent + f'{tx}.000 9.500 {ty}.000'.encode() + tail
                cnt += 1
            k += 1
        changed[pid] = (old, (tx, ty), cnt)
        P(f'省 {pid}: 替换 {cnt} 行 -> ({tx}.000, {ty}.000)')
        P(f'   原值样例: {old[0] if old else "(无)"}')
    i += 1

new_data = b'\n'.join(lines)
open(OUT, 'wb').write(new_data)
P('')
P(f'新文件 {len(new_data):,} B  md5={hashlib.md5(new_data).hexdigest()}')
P(f'字节数差 {len(new_data) - len(data):+d}')
P(f'产物 -> {OUT}')

# 字节级自检：只有这 14 个块内的行可变
ol = data.split(b'\n'); nl = new_data.split(b'\n')
P('')
P('=== 字节级自检 ===')
P(f'行数 {len(ol)} vs {len(nl)}  一致={len(ol)==len(nl)}')
diff = [i for i, (x, y) in enumerate(zip(ol, nl)) if x != y]
P(f'发生变化的行数 = {len(diff)}  （应为 {14*6} = 84）')
P(f'变化行号: {diff}')

open(REP, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))

# -*- coding: utf-8 -*-
"""xcross.py —— X-crossing 定位与修复 + 15州省块引用检查
默认只分析；--apply 时写回两个副本的 provinces.bmp（先备份）
"""
import os, re, sys, glob, struct, collections, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
COPIES = [('仓库', G),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
APPLY = '--apply' in sys.argv

# 颜色表
color_of = {}
colors = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            pid = int(c[0])
        except ValueError:
            continue
        colors[(int(c[1]), int(c[2]), int(c[3]))] = pid
        color_of[pid] = (int(c[1]), int(c[2]), int(c[3]))
gk = {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            gk[int(c[0])] = c[4]
        except ValueError:
            pass

raw = bytearray(open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read())
off = struct.unpack('<I', raw[10:14])[0]
W, Hh = struct.unpack('<ii', raw[18:26])
RB = W * 3

def getpix(x, z):
    i = off + z * RB + x * 3
    return colors.get((raw[i + 2], raw[i + 1], raw[i]))

def grid(x0, z0, w=16, h=8):
    for z in range(z0, z0 + h):
        row = []
        for x in range(x0, x0 + w):
            p = getpix(x, z)
            row.append(f'{p:>5}' if p is not None else '  ???')
        print('    z=' + f'{z:<4}', ' '.join(row))

print('=== 候选窗口 1: (4095,480) 直读空间 ===')
grid(4088, 472, 8, 16)
print()
print('=== 候选窗口 2: (4095, 2048-480=1568) 镜像空间 ===')
grid(4088, 1560, 8, 16)

# 找 X 交叉：2x2 内 a==d, b==c, a!=b
print()
print('=== X 交叉检测（两个窗口各扫一遍）===')
found = []
for name, z0 in (('直读', 480), ('镜像', 1568)):
    for z in range(z0 - 12, z0 + 12):
        for x in range(4095 - 12, 4095):
            if not (0 <= x < W - 1 and 0 <= z < Hh - 1):
                continue
            a, b = getpix(x, z), getpix(x + 1, z)
            c, d = getpix(x, z + 1), getpix(x + 1, z + 1)
            if a is not None and b is not None and a == d and b == c and a != b:
                found.append((name, x, z, a, b))
    # 也扫 x=4094 左边的
    for z in range(z0 - 12, z0 + 12):
        for x in range(4080, 4095):
            if not (0 <= x < W - 1 and 0 <= z < Hh - 1):
                continue
            a, b = getpix(x, z), getpix(x + 1, z)
            c, d = getpix(x, z + 1), getpix(x + 1, z + 1)
            if a is not None and b is not None and a == d and b == c and a != b:
                found.append((name, x, z, a, b))
# 去重
seen = set()
uniq = []
for f in found:
    k = (f[1], f[2])
    if k not in seen:
        seen.add(k)
        uniq.append(f)
print(f'  找到 {len(uniq)} 处:')
for name, x, z, a, b in uniq:
    ka, kb = gk.get(a), gk.get(b)
    print(f'   [{name}] 2x2 原点 ({x},{z}): A={a}({ka}) B={b}({kb})  图案: {a} {b} / {b} {a}')

if uniq and APPLY:
    # 修复：把 2x2 里的一格改成破环（选 A 的右下格改 A→? 或把 B 改 A）
    st = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    BD = os.path.join(ROOT, '.backups', f'xcross_{stamp}' if False else f'xcross_{st}')
    os.makedirs(BD, exist_ok=True)
    # 取第一处（按坐标去重后应只有一处）
    name, x, z, a, b = uniq[0]
    # 平局判断：把 (x+1, z+1)=A 改成 B 还是把 (x, z)=A 改 B？
    # 标准做法：选 A 一侧，改成 B——优先改 (x, z+1)=B → 改成 A，使 B 成 L?
    # 更稳：令 (x, z) = b  → 2x2 变成 b b / b a  （B三格,A一角，对角消失）
    cand = []
    for (cx, cz, newp) in ((x, z, b), (x + 1, z + 1, b), (x + 1, z, a), (x, z + 1, a)):
        cand.append((cx, cz, newp))
    # 选不孤立任何一方的：优先改 A 成 B 后检查 A 连通 & B 连通
    def neighbors4(cx, cz, pid):
        n = 0
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if getpix(cx + dx, cz + dz) == pid:
                n += 1
        return n
    best = None
    for (cx, cz, newp) in cand:
        old = getpix(cx, cz)
        # 改后：old 侧是否还有 4 连通（该像素原是同侧唯一连接点？）
        cnt_old = neighbors4(cx, cz, old)  # 邻域里同侧数量（不数自己）
        if cnt_old >= 2:
            best = (cx, cz, newp, old)
            break
    if not best:
        best = (x, z, b, a)
    cx, cz, newp, old = best
    print(f'  修复方案: 像素 ({cx},{cz}) {old}({gk.get(old)}) → {newp}({gk.get(newp)})')
    for tag, base in COPIES:
        p = os.path.join(base, 'map', 'provinces.bmp')
        raw2 = bytearray(open(p, 'rb').read())
        r, g, bb = color_of[newp]
        i = off + cz * RB + cx * 3
        raw2[i], raw2[i + 1], raw2[i + 2] = bb, g, r
        shutil.copy2(p, os.path.join(BD, f'{tag}_provinces.bmp'))
        open(p, 'wb').write(bytes(raw2))
        print(f'  {tag}: 已写回')
    # 验证
    print()
    print('=== 修复后窗口验证 ===')
    grid(cx - 3, cz - 3, 8, 8)
    # 复查该窗口 X 交叉
    still = 0
    for zz in range(cz - 6, cz + 6):
        for xx in range(cx - 6, cx + 6):
            a2, b2 = getpix(xx, zz), getpix(xx + 1, zz)
            c2, d2 = getpix(xx, zz + 1), getpix(xx + 1, zz + 1)
            if a2 is not None and a2 == d2 and b2 == c2 and a2 != b2:
                still += 1
    print(f'  窗口内剩余 X 交叉: {still}')
else:
    print()
    print('（DRY：加 --apply 写回）' if uniq else '  窗口内没找到 X 交叉图案（可能需要扩大范围）')

# ---- 15 州省块引用检查 ----
print()
print('=== 15 州 省块（PROV = { ... }）引用是否在州内 ===')
bad15 = [76, 82, 223, 246, 269, 284, 311, 500, 560, 564, 569, 584, 587, 590, 607]
s2p = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        s2p[int(m.group(1))] = [int(x) for x in re.findall(r'\d+', m2.group(1))]

for s in bad15:
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{s}*.txt'))
          if re.match(rf'^{s}(\(|-)', os.path.basename(f))]
    if not fs:
        continue
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    own = set(s2p.get(s, []))
    refs = [(int(a), b.strip()[:30]) for a, b in re.findall(r'(?m)^\s*(\d+)\s*=\s*\{([^}]*)\}', t)]
    out = []
    for pid, blk in refs:
        out.append(f'{pid}{"✓" if pid in own else "★不在州内"}')
    print(f'  s{s}: 省块 {len(refs)} 个: {out}')
print()
print('=== 对照 ===')
for s in (1, 5, 179, 400, 600):
    fs = [f for f in glob.glob(os.path.join(G, 'history', 'states', f'{s}*.txt'))
          if re.match(rf'^{s}(\(|-)', os.path.basename(f))]
    if not fs:
        continue
    t = open(fs[0], encoding='utf-8-sig', errors='replace').read()
    own = set(s2p.get(s, []))
    refs = [(int(a), b.strip()[:30]) for a, b in re.findall(r'(?m)^\s*(\d+)\s*=\s*\{([^}]*)\}', t)]
    out = []
    for pid, blk in refs:
        out.append(f'{pid}{"✓" if pid in own else "★不在州内"}')
    print(f'  s{s}: 省块 {len(refs)} 个: {out}')

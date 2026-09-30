# -*- coding: utf-8 -*-
"""
五处飞地最小改动（用户指定 A 方案）：
  403: 21→242、4313: 61→778、2643: 203→231、3203: 379→382、118: 435→816
携带省级建筑块与胜利点。
"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

MOVES = [(403, 21, 242), (4313, 61, 778), (2643, 203, 231), (3203, 379, 382), (118, 435, 816)]

s2p, s2o, raw = {}, {}, {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', newline='').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    s2o[sid] = mo.group(1) if mo else None
    s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
    raw[sid] = t

print('=== 前置校验 ===')
for p, src, dst in MOVES:
    ok1 = p in s2p.get(src, [])
    print(f'  省 {p}: 在 state {src}({s2o.get(src)})? {ok1}  → state {dst}({s2o.get(dst)})'
          f'（目标州现 {len(s2p.get(dst, []))} 省）')
    assert ok1, f'省 {p} 不在 state {src}'

bdir = os.path.join(ROOT, '.backups', 'enclave_min_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
touched = set()
for p, src, dst in MOVES:
    touched.add(src)
    touched.add(dst)
    s2p[src].remove(p)
    if p not in s2p[dst]:
        s2p[dst].append(p)

PB = re.compile(r'\t\t\t(\d+) = \{\r\n(?:\t\t\t\t[^\r\n]*\r\n)+\t\t\t\}')
work = {s: raw[s] for s in touched}
for p, src, dst in MOVES:
    for m in PB.finditer(work[src]):
        if int(m.group(1)) == p:
            work[src] = work[src].replace(m.group(0) + '\r\n', '')
            bm = re.search(r'\t\tbuildings = \{', work[dst])
            if bm:
                depth, i, end = 0, bm.end() - 1, None
                while i < len(work[dst]):
                    if work[dst][i] == '{':
                        depth += 1
                    elif work[dst][i] == '}':
                        depth -= 1
                        if depth == 0:
                            end = i
                            break
                    i += 1
                work[dst] = work[dst][:end] + m.group(0) + '\r\n' + work[dst][end:]
            print(f'  省 {p}: 携带省级建筑块 → state {dst}')
            break

for sid in sorted(touched):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = re.sub(r'(provinces = \{\r?\n\t\t)[^\r\n]*(\r?\n\t\})',
               lambda m: f'{m.group(1)}{" ".join(map(str, sorted(s2p[sid])))}{m.group(2)}', work[sid])
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)
print(f'\n已写入 {len(touched)} 个州文件，备份 {bdir}')

print()
print('=== 改动后各州 ===')
for sid in sorted(touched):
    tag = s2o.get(sid)
    print(f'  state {sid:4d}({tag}): {len(s2p[sid])} 省 {sorted(s2p[sid])}')

print()
print('=== 全图：空州 / 单省陆州 ===')
empty = sorted(s for s, ps in s2p.items() if not ps)
print(f'  空州 {len(empty)} 个: {empty}')
one = sorted(s for s, ps in s2p.items() if len(ps) == 1 and s2o.get(s))
print(f'  单省陆州 {len(one)} 个: {one}')

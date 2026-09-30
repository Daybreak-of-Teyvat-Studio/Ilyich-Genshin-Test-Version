# -*- coding: utf-8 -*-
"""
飞地修复（仅同国变更，不动国界）：
  3499: 54→59、4686: 74→530、2643: 203→231、461: 514→527、1154: 529→544
携带省级建筑块与胜利点；改后同步 buildings.txt 的州列。
"""
import os, re, sys, shutil, datetime, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

MOVES = [(3499, 54, 59), (4686, 74, 530), (2643, 203, 231), (461, 514, 527), (1154, 529, 544)]

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

# 前置校验：同国
for p, a, b in MOVES:
    assert p in s2p[a], f'省 {p} 不在 state {a}'
    assert s2o[a] == s2o[b], f'state {a}({s2o[a]}) 与 {b}({s2o[b]}) 不同国，跳过'
print('前置校验通过：5 处均为同国迁移')

PB = re.compile(r'\t\t\t(\d+) = \{\r\n(?:\t\t\t\t[^\r\n]*\r\n)+\t\t\t\}')


def extract_prov_block(t, pid):
    """取出某省的省级建筑块（含前后换行）"""
    for m in PB.finditer(t):
        if int(m.group(1)) == pid:
            return m.group(0)
    return None


def strip_prov_block(t, pid):
    t2 = re.sub(rf'\t\t\t{pid} = \{{\r\n(?:\t\t\t\t[^\r\n]*\r\n)+\t\t\t\}}\r\n', '', t)
    return t2


def extract_vp(t, pid):
    for m in re.finditer(r'victory_points = \{([^}]*)\}', t):
        v = m.group(1).split()
        out = []
        for i in range(0, len(v) - 1, 2):
            if int(v[i]) != pid:
                out.append((int(v[i]), int(v[i + 1])))
        if len(out) != len(v) // 2:
            return out
    return None


bdir = os.path.join(ROOT, '.backups', 'enclave_same_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
touched = set()
for p, src, dst in MOVES:
    touched.add(src)
    touched.add(dst)
    s2p[src].remove(p)
    if p not in s2p[dst]:
        s2p[dst].append(p)

work = {sid: raw[sid] for sid in touched}
# 省级块与 VP 搬迁
for p, src, dst in MOVES:
    blk = extract_prov_block(work[src], p)
    if blk:
        work[src] = strip_prov_block(work[src], p)
        # 插入目标州 buildings 块末尾
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
            work[dst] = work[dst][:end] + blk + '\r\n' + work[dst][end:]
        print(f'  省 {p}: 携带省级建筑块')
    nv = extract_vp(work[src], p)
    if nv is not None:
        line = ('victory_points = { ' + ' '.join(f'{a} {b}' for a, b in sorted(nv)) + ' }') if nv else None
        work[src] = re.sub(r'victory_points = \{[^}]*\}', line, work[src]) if line else \
            re.sub(r'\r\n\t\tvictory_points = \{[^}]*\}', '', work[src])
        print(f'  省 {p}: 携带胜利点')

for sid in sorted(touched):
    fp = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(fp, os.path.join(bdir, os.path.basename(fp)))
    t = re.sub(r'(provinces = \{\r\n\t\t)[^\r\n]*(\r\n\t\})',
               lambda m: f'{m.group(1)}{" ".join(map(str, sorted(s2p[sid])))}{m.group(2)}', work[sid])
    with open(fp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)
print(f'\n已写入 {len(touched)} 个州文件，备份 {bdir}')

# 复验：这 5 处不再孤立
for p, src, dst in MOVES:
    print(f'  省 {p}: state {src} → {dst}({s2o[dst]})  '
          f'源州剩余 {sorted(s2p[src])}  目标州 {sorted(s2p[dst])}')

# -*- coding: utf-8 -*-
"""
Gamma 版地块调整工具。

用法：
  python gamma_state_edits.py 指令文件.txt          # 应用文件里的指令
  python gamma_state_edits.py 指令文件.txt --dry    # 只算不写
  python gamma_state_edits.py "918 2354+416" "423+FAV"

指令格式（与主写手写的一致）：
  918 2354+416   把省 918、2354 转到 state 416（右侧是数字 = 转省）
  423+FAV        state 423 的 owner 改为 FAV，核心清空后只留 FAV（右侧是 tag = 改归属）
  # 开头为注释

规则（已确认）：
  · 转省时，该省挂着的省级建筑块与胜利点一起搬到新州
  · 改归属时，owner = TAG，add_core_of 只留 TAG（原核心清掉）
  · 文件保持 CRLF 行尾、tab 缩进、无 BOM；provinces 保持升序
  · 写盘前自动备份到 .backups/gamma_states_<时间戳>/
"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
ST = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')

# ---------------------------------------------------------------- 指令解析
def parse_cmd(s):
    s = s.strip()
    if not s or s.startswith('#'):
        return None
    m = re.fullmatch(r'([\d\s]+)\s*\+\s*([A-Za-z_]+|\d+)', s)
    if not m:
        raise ValueError(f'看不懂的指令: {s!r}')
    lhs = [int(x) for x in m.group(1).split()]
    rhs = m.group(2)
    if rhs.isdigit():                       # 转省
        return ('move', lhs, int(rhs))
    if len(lhs) != 1:                       # 改归属只能指定一个州
        raise ValueError(f'改归属指令左侧只能是单个 state_id: {s!r}')
    return ('own', lhs[0], rhs.upper())


# ---------------------------------------------------------------- 文件读写
def path_of(i):
    return os.path.join(ST, f'{i}-State_{i}.txt')


def load(i):
    return open(path_of(i), encoding='utf-8-sig', newline='').read()


def dump(i, t):
    with open(path_of(i), 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)


def block_end(t, brace):
    """brace 指向 '{'，返回配对的 '}' 下标"""
    depth, i = 0, brace
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError('花括号不配对')


PROV_BLK = re.compile(r'\t\t\t(\d+) = \{\r\n((?:\t\t\t\t[^\r\n]*(?:\r\n))+)+\t\t\t\}')
H_OPEN = re.compile(r'\thistory = \{')
B_OPEN = re.compile(r'\t\tbuildings = \{')


def get_provs(t):
    m = re.search(r'provinces = \{\r?\n\t\t([^\r\n]*)\r?\n\t\}', t)
    if not m:
        raise ValueError('找不到 provinces 块')
    return [int(x) for x in m.group(1).split()]


def set_provs(t, pl):
    return re.sub(r'(provinces = \{\r?\n\t\t)[^\r\n]*(\r?\n\t\})',
                  lambda m: f'{m.group(1)}{" ".join(map(str, pl))}{m.group(2)}', t)


def get_buildings(t):
    bm = B_OPEN.search(t)
    if not bm:
        return None
    o = bm.end() - 1
    return o, block_end(t, o)


def get_prov_blocks(t):
    b = get_buildings(t)
    if not b:
        return []
    o, c = b
    body = t[o:c + 1]
    return [(int(m.group(1)), t[o + m.start():o + m.end()], o + m.start(), o + m.end())
            for m in PROV_BLK.finditer(body)]


def del_prov_block(t, pid):
    for p, blk, s, e in get_prov_blocks(t):
        if p == pid:
            return t[:t.rfind('\r\n', 0, s)] + t[e:]
    return t


def add_prov_block(t, pid, lines):
    blk = '\t\t\t%d = {\r\n%s\r\n\t\t\t}' % (
        pid, '\r\n'.join('\t\t\t\t' + l for l in lines))
    pb = get_prov_blocks(t)
    if pb:
        last = max(pb, key=lambda x: x[3])
        return t[:last[3]] + '\r\n' + blk + t[last[3]:]
    o, c = get_buildings(t)          # 没有省级块：插到 buildings 收尾前
    return t[:c] + blk + '\r\n\t\t' + t[c:]


def get_vps(t):
    m = re.search(r'victory_points = \{([^}]*)\}', t)
    if not m:
        return []
    v = m.group(1).split()
    return list(zip(map(int, v[0::2]), map(int, v[1::2])))


def set_vps(t, vps):
    if re.search(r'victory_points = \{[^}]*\}', t):
        if not vps:
            return re.sub(r'\r\n\t\tvictory_points = \{[^}]*\}', '', t)
        return re.sub(r'victory_points = \{[^}]*\}',
                      'victory_points = { ' + ' '.join(f'{p} {n}' for p, n in sorted(vps)) + ' }',
                      t)
    if not vps:
        return t
    # 原本没有 victory_points：作为独立一行插到 history 块收尾 } 之前（行首对齐到 \t\t）
    o = H_OPEN.search(t).end() - 1
    c = block_end(t, o)
    ls = t.rfind('\r\n', 0, c) + 2                      # 收尾 } 所在行的行首
    return (t[:ls] + '\t\tvictory_points = { ' +
            ' '.join(f'{p} {n}' for p, n in sorted(vps)) + ' }\r\n' + t[ls:])


def set_owner(t, tag):
    t = re.sub(r'\t\towner = \w+', f'\t\towner = {tag}', t, count=1)
    t = re.sub(r'\r\n\t\tadd_core_of = \w+', '', t)          # 清掉全部原核心
    return re.sub(r'(\t\towner = ' + tag + r')',
                  rf'\1\r\n\t\tadd_core_of = {tag}', t, count=1)


# ---------------------------------------------------------------- 主流程
argv = [a for a in sys.argv[1:] if not a.startswith('--')]
DRY = '--dry' in sys.argv
parts = []
for a in argv:
    if os.path.isfile(a):
        parts.append(open(a, encoding='utf-8-sig').read())
    else:
        parts.append(a)
text = re.sub(r'#[^\n]*', '', '\n'.join(parts))          # 去掉注释
# 分隔语义：句点/分号 = 指令分隔；逗号 = 并列省（等同空格，
# 如 "395,524,1252+464" = 三省同给 464）
tokens = []
for seg in re.split(r'[.;]+', text):
    seg = seg.replace(',', ' ').replace('\uff0c', ' ').strip()   # 全角逗号同
    if seg:
        tokens.append(seg)
CMDS = [parse_cmd(x) for x in tokens]
if not CMDS:
    print('没有指令'); sys.exit(0)

states, p2s = {}, {}
for f in os.listdir(ST):
    i = int(f.split('-')[0])
    states[i] = load(i)
    for p in get_provs(states[i]):
        assert p not in p2s, f'省 {p} 重复归属 {p2s[p]}/{i}'
        p2s[p] = i
print(f'载入 {len(states)} 州 / {len(p2s)} 省，指令 {len(CMDS)} 条')
for kind, a, b in CMDS:
    print('  ', '转省' if kind == 'move' else '改归属', a, '->', b)

changed, log, errs = {}, [], []
prov_moves = {}          # 省 -> (原州, 新州)，用于同步 map/buildings.txt

for cmd in CMDS:
    if cmd[0] == 'move':
        _, pl, dst = cmd
        if dst not in states:
            errs.append(f'state {dst} 不存在'); continue
        for p in pl:
            if p not in p2s:
                errs.append(f'省 {p} 不存在于任何州'); continue
            src = p2s[p]
            if src == dst:
                log.append(f'省 {p} 已在 state {dst}，跳过'); continue
            ts, td = changed.get(src, states[src]), changed.get(dst, states[dst])
            moved, vpmoved = None, None
            for bp, blk, s, e in get_prov_blocks(ts):
                if bp == p:
                    moved = [l.strip() for l in blk.split('\r\n')[1:-1]]
                    ts = del_prov_block(ts, p)
                    break
            if moved:
                td = add_prov_block(td, p, moved)
            for vp in [v for v in get_vps(ts) if v[0] == p]:
                ts = set_vps(ts, [v for v in get_vps(ts) if v[0] != p])
                td = set_vps(td, get_vps(td) + [vp])
                vpmoved = vp
            ts = set_provs(ts, sorted(x for x in get_provs(ts) if x != p))
            td = set_provs(td, sorted(get_provs(td) + [p]))
            changed[src], changed[dst] = ts, td
            p2s[p] = dst
            prov_moves[p] = (src, dst)
            log.append(f'省 {p}: {src} -> {dst}'
                       + (f' 带建筑 {moved}' if moved else '')
                       + (f' 带胜利点 {vpmoved}' if vpmoved else ''))
    else:
        _, sid, tag = cmd
        if sid not in states:
            errs.append(f'state {sid} 不存在'); continue
        t = changed.get(sid, states[sid])
        old = re.search(r'\t\towner = (\w+)', t)
        oldc = re.findall(r'\t\tadd_core_of = (\w+)', t)
        changed[sid] = set_owner(t, tag)
        log.append(f'state {sid}: owner {old.group(1) if old else "?"} -> {tag}'
                   f'，核心 {oldc} -> [{tag}]')

for l in log:
    print(' ', l)
for e in errs:
    print('  ! ', e)

if changed and not DRY:
    bdir = os.path.join(ROOT, '.backups', 'gamma_states_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(bdir, exist_ok=True)
    for i, t in changed.items():
        shutil.copy2(path_of(i), os.path.join(bdir, os.path.basename(path_of(i))))
        dump(i, t)
    print(f'\n已写入 {len(changed)} 个文件，原件备份于 {bdir}')
else:
    print('\n[DRY] 未写盘')

# 同步 map/buildings.txt —— 省转州后不同步，游戏会忽略该建筑，沿海省会缺少港口并崩溃
if prov_moves:
    from gamma_buildings_sync import sync as sync_buildings
    try:
        # 传入内存里的省->州映射（DRY 时磁盘上的 state 文件还没更新）
        sync_buildings(prov_moves, dry=DRY, state_map=p2s)
    except Exception as e:                     # noqa: BLE001
        print(f'  !! buildings.txt 同步失败: {e}')

# 事后校验（DRY 时看内存里的结果）
errs2 = []
p2s2 = {}
for f in os.listdir(ST):
    i = int(f.split('-')[0])
    t = changed.get(i, load(i)) if DRY else load(i)
    if t.startswith('\ufeff'):
        errs2.append(f'{i}: BOM')
    if re.search(r'(?m)^ +', t):
        errs2.append(f'{i}: 行首空格')
    if t.count('{') != t.count('}'):
        errs2.append(f'{i}: 花括号不配对')
    if not DRY:
        rb = open(path_of(i), 'rb').read()
        if rb.count(b'\n') != rb.count(b'\r\n'):
            errs2.append(f'{i}: 行尾不是纯 CRLF')
    pl = get_provs(t)
    if pl != sorted(pl):
        errs2.append(f'{i}: provinces 未升序')
    if not pl:
        errs2.append(f'{i}: provinces 为空')
    pls = set(pl)
    for pid, _v in get_vps(t):          # 胜利点必须落在本州省份上
        if pid not in pls:
            errs2.append(f'{i}: 胜利点省 {pid} 不在本州 provinces')
    for pid, _b, _s, _e in get_prov_blocks(t):   # 省级建筑块同理
        if pid not in pls:
            errs2.append(f'{i}: 建筑块省 {pid} 不在本州 provinces')
    for p in pl:
        if p in p2s2:
            errs2.append(f'{i}: 省 {p} 与 {p2s2[p]} 冲突')
        p2s2[p] = i
print(f'校验：{len(errs2)} 个问题 / 省 {len(p2s2)} 个')
for e in errs2[:20]:
    print('  !', e)

for i in sorted(changed):
    t = changed[i] if DRY else load(i)
    print(f'\n### {("目标 " if DRY else "")}state {i}：')
    for line in t.split('\r\n'):
        if line.strip():
            print('  ', line)

# -*- coding: utf-8 -*-
"""fix_state_errors.py —— 修复两类州文件错误
1) 5 个无效 dockyard（州无沿海省）：s15/s54/s125/s238/s249 删除 dockyard 行
2) 9 处错州 naval_base 块：
   搬迁（新州无）: 1772 s15→s384、1368 s152→s150、2733 s249→s237、182 s415→s405、1157 s470→s489
   删除（新州已有同块）: 78/1821 删 s186、2001 删 s204、356 删 s208
仓库 + 部署副本；先备份；回读验证"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]

DOCKYARD_STATES = [15, 54, 125, 238, 249]
MOVE = [(1772, 15, 384), (1368, 152, 150), (2733, 249, 237), (182, 415, 405), (1157, 470, 489)]
DEL = [(78, 186), (1821, 186), (2001, 204), (356, 208)]

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'stateerr_{stamp}')
os.makedirs(BD, exist_ok=True)


def load(p):
    raw = open(p, 'rb').read()
    return raw, raw.decode('utf-8-sig')


def save(p, t, bom):
    open(p, 'wb').write(((b'\xef\xbb\xbf' if bom else b'') + t.encode('utf-8')))


def sfile(base, sid):
    return glob.glob(os.path.join(base, 'history', 'states', f'{sid}-State_*.txt'))[0]


def buildings_close(t):
    """buildings 块闭合 } 的下标"""
    m = re.search(r'\bbuildings\s*=\s*\{', t)
    depth, i = 0, m.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError('buildings 未闭合')


for tag, base in COPIES:
    touched = set()
    # 1) dockyard 删除
    for sid in DOCKYARD_STATES:
        p = sfile(base, sid)
        if tag == '仓库':
            shutil.copy2(p, os.path.join(BD, os.path.basename(p)))
        raw, t = load(p)
        t2, n = re.subn(r'(?m)^[ \t]*dockyard[ \t]*=[ \t]*\d+[ \t]*\r?\n?', '', t)
        assert n == 1, f's{sid} dockyard 数 {n}'
        save(p, t2, raw[:3] == b'\xef\xbb\xbf')
        touched.add(sid)
    print(f'{tag}: 删 dockyard ×{len(DOCKYARD_STATES)}')

    # 2) 删除重复块
    for pid, sid in DEL:
        p = sfile(base, sid)
        if tag == '仓库':
            shutil.copy2(p, os.path.join(BD, os.path.basename(p)))
        raw, t = load(p)
        t2, n = re.subn(r'(?m)^[ \t]*' + str(pid) + r'[ \t]*=[ \t]*\{[^}]*\}[ \t]*\r?\n?', '', t)
        assert n == 1, f'p{pid}@s{sid} 数 {n}'
        save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'{tag}: 删重复块 ×{len(DEL)}')

    # 3) 搬迁块
    for pid, old_s, new_s in MOVE:
        # 从旧州删
        p = sfile(base, old_s)
        if tag == '仓库':
            shutil.copy2(p, os.path.join(BD, os.path.basename(p)))
        raw, t = load(p)
        m = re.search(r'(?m)^([ \t]*)' + str(pid) + r'[ \t]*=[ \t]*\{([^}]*)\}', t)
        assert m, f'p{pid} 在 s{old_s} 未找到'
        inner = m.group(2)
        t2 = t[:m.start()] + t[m.end():]
        t2 = re.sub(r'(?m)^\r?\n', '', t2, count=0)
        save(p, t2, raw[:3] == b'\xef\xbb\xbf')
        # 在新州 buildings 块闭合前插入
        p2 = sfile(base, new_s)
        raw2, t3 = load(p2)
        close = buildings_close(t3)
        ls = t3.rfind('\n', 0, close) + 1
        block = f'\t\t\t{pid} = {{{inner}}}\r\n'
        t3 = t3[:ls] + block + t3[ls:]
        save(p2, t3, raw2[:3] == b'\xef\xbb\xbf')
        print(f'  {tag}: 块 p{pid} s{old_s}→s{new_s}（{inner.strip()}）')

print()
# ---- 回读验证 ----
kind, coastal = {}, {}
for l in open(os.path.join(COPIES[0][1], 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 6 and a[0].strip().isdigit() and int(a[0]) > 0:
        kind[int(a[0])], coastal[int(a[0])] = a[4], (a[5].strip().lower() == 'true')

for tag, base in COPIES:
    print(f'=== {tag} 验证 ===')
    err = 0
    for sid in DOCKYARD_STATES:
        p = sfile(base, sid)
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        dy = re.search(r'dockyard\s*=\s*\d+', t)
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        provs = [int(x) for x in pm.group(1).split()]
        coast = [q for q in provs if coastal.get(q)]
        ok = dy is None and not coast
        err += not ok
        print(f'  s{sid}: dockyard={"还在!" if dy else "已删"} 沿海省={coast} {"✓" if ok else "✗"}')
    for pid, old_s, new_s in MOVE:
        told = open(sfile(base, old_s), encoding='utf-8-sig', errors='replace').read()
        tnew = open(sfile(base, new_s), encoding='utf-8-sig', errors='replace').read()
        ok_old = re.search(r'(?m)^\s*' + str(pid) + r'\s*=', told) is None
        ok_new = re.search(r'(?m)^\s*' + str(pid) + r'\s*=\s*\{[^}]*naval_base\s*=\s*2', tnew) is not None
        ok = ok_old and ok_new
        err += not ok
        print(f'  块 p{pid}: 旧州已无={ok_old} 新州已有={ok_new} {"✓" if ok else "✗"}')
    for pid, sid in DEL:
        t = open(sfile(base, sid), encoding='utf-8-sig', errors='replace').read()
        ok = re.search(r'(?m)^\s*' + str(pid) + r'\s*=', t) is None
        err += not ok
        print(f'  删 p{pid}@s{sid}: {"✓" if ok else "✗"}')
    print(f'  错误数: {err}')

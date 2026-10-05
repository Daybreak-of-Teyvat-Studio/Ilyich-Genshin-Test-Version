# -*- coding: utf-8 -*-
"""fix_vp4.py —— 补写 4 条 VP：s727{1343:15} s703{4216:15} s750{1416:15}{1442:15} + 2 个本地化 key
字节级 CRLF/缩进/BOM 保持，先备份，后回读验证"""
import os, re, sys, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
VP_F = os.path.join(MOD, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
JOBS = {727: [(1343, 15)], 703: [(4216, 15)], 750: [(1416, 15), (1442, 15)]}
LOC_ADD = [(1416, '雨的尽头'), (1442, '晴雨的经纬')]

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'vp4_{stamp}')
os.makedirs(BD, exist_ok=True)
print(f'备份: {BD}')


def history_close(t):
    m = re.search(r'\bhistory\s*=\s*\{', t)
    depth, i = 0, m.end() - 1
    while True:
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1


for sid, adds in JOBS.items():
    p = os.path.join(ST, f'{sid}-State_{sid}.txt')
    shutil.copy2(p, BD)
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    crlf = b'\r\n'
    existing = {int(x) for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t)
                for x in [vm.group(1).split()] for x in x[::2]}
    dup = [pid for pid, _ in adds if pid in existing]
    if dup:
        print(f'  s{sid}: 已有 VP 省 {dup}，跳过这些')
        adds = [(pid, v) for pid, v in adds if pid not in dup]
    if not adds:
        continue
    ins = ''.join(f'\t\tvictory_points = {{ {pid} {val} }}\r\n' for pid, val in adds)
    ls = t.rfind('\n', 0, history_close(t)) + 1
    t2 = t[:ls] + ins + t[ls:]
    data = t2.encode('utf-8')
    open(p, 'wb').write((b'\xef\xbb\xbf' + data) if raw[:3] == b'\xef\xbb\xbf' else data)
    seg = open(p, 'rb').read().split(b'victory_points')[-1][:60]
    print(f'  s{sid}: 加 ' + ', '.join(f'p{pid}={v}' for pid, v in adds) + f'；CRLF={crlf in seg}')

raw = open(VP_F, 'rb').read()
has_bom = raw[:3] == b'\xef\xbb\xbf'
t = raw.decode('utf-8-sig')
nl = '\r\n' if '\r\n' in t else '\n'
lines = t.split(nl)
have = {int(m.group(1)) for l in lines if (m := re.match(r'^\s*VICTORY_POINTS_(\d+):', l))}
out = list(lines)
added = 0
for pid, nm in LOC_ADD:
    if pid in have:
        print(f'  VICTORY_POINTS_{pid} 已存在，跳过')
        continue
    out.append(f' VICTORY_POINTS_{pid}:0 "{nm}"')
    added += 1
open(VP_F, 'wb').write(((b'\xef\xbb\xbf' if has_bom else b'') + nl.join(out).encode('utf-8')))
print(f'VP 本地化: 加 {added} 行')

# 回读验证
print()
print('=== 回读验证 ===')
for sid, adds in JOBS.items():
    t = open(os.path.join(ST, f'{sid}-State_{sid}.txt'), encoding='utf-8-sig').read()
    got = {int(xs[i]): int(xs[i + 1])
           for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t)
           for xs in [vm.group(1).split()]
           for i in range(0, len(xs) - 1, 2)}
    want = dict(adds)
    ok = all(got.get(pid) == v for pid, v in want.items())
    print(f'  s{sid}: {got} -> {"✓" if ok else "✗"}')
t = open(VP_F, encoding='utf-8-sig').read()
for pid, nm in LOC_ADD:
    print(f'  VICTORY_POINTS_{pid}: {"✓" if f"VICTORY_POINTS_{pid}:" in t and f'"{nm}"' in t else "✗"}')

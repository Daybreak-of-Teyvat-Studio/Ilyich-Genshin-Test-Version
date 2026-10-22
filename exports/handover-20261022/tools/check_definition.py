# -*- coding: utf-8 -*-
"""definition.csv 完整性检查（nudge 的"地图定义文件"就是它）"""
import os, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEF = os.path.join(G, 'map', 'definition.csv')

raw = open(DEF, 'rb').read()
print(f'字节 {len(raw)}  BOM={raw[:3] == b"\xef\xbb\xbf"}  '
      f'首字节={raw[:6].hex()}')
t = raw.decode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8', errors='replace')
lines = t.split('\r\n') if '\r\n' in t else t.split('\n')
print(f'行数 {len(lines)}  行尾 CRLF={t.count(chr(13)+chr(10))} LF={t.count(chr(10))}')

# 首行原样
print(f'首行 repr: {repr(lines[0])[:120]}')
print(f'第2行 repr: {repr(lines[1])[:120]}')

# 字段数分布
cnt = collections.Counter()
bad_rows = []
ids = []
seen = set()
for i, l in enumerate(lines):
    if not l.strip():
        cnt['空行'] += 1
        continue
    a = l.split(';')
    cnt[len(a)] += 1
    if len(a) != 8:
        if len(bad_rows) < 10:
            bad_rows.append((i + 1, l[:100]))
        continue
    if not a[0].strip().isdigit():
        if len(bad_rows) < 10:
            bad_rows.append((i + 1, 'id 非数字: ' + l[:80]))
        continue
    pid = int(a[0])
    if pid in seen:
        if len(bad_rows) < 10:
            bad_rows.append((i + 1, f'重复 id {pid}'))
    seen.add(pid)
    ids.append(pid)
print(f'\n字段数分布: {dict(cnt.most_common())}')
print(f'id 数 {len(ids)} 范围 {min(ids)}-{max(ids)} 重复 {len(ids)-len(seen)}')
if bad_rows:
    print('\n问题行:')
    for ln, txt in bad_rows:
        print(f'  行 {ln}: {txt}')
else:
    print('无问题行')

# 与 mod 其他 map 文件的时间戳
print()
for f in ('definition.csv', 'provinces.bmp', 'terrain.bmp', 'heightmap.bmp',
          'rivers.bmp', 'adjacencies.csv', 'islands.txt', 'buildings.txt'):
    p = os.path.join(G, 'map', f)
    if os.path.exists(p):
        import datetime
        print(f'  {f:18s} {os.path.getsize(p):>12,}  {datetime.datetime.fromtimestamp(os.path.getmtime(p))}')
    else:
        print(f'  {f:18s} 不存在')

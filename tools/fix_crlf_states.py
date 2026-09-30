# -*- coding: utf-8 -*-
"""① 41 个海州文件 LF → CRLF；② gamma_state_edits.py 的正则容错 \r?\n"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
ST = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')

# ① 全量检查换行并统一为 CRLF
bdir = os.path.join(ROOT, '.backups', 'crlf_fix_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
fixed = []
for f in sorted(os.listdir(ST)):
    if not f.endswith('.txt'):
        continue
    p = os.path.join(ST, f)
    raw = open(p, 'rb').read()
    lf, crlf = raw.count(b'\n'), raw.count(b'\r\n')
    if lf != crlf:                      # 有裸 LF
        shutil.copy2(p, os.path.join(bdir, f))
        t = raw.decode('utf-8-sig')
        t = '\r\n'.join(l.replace('\r', '') for l in t.split('\n'))
        open(p, 'wb').write(t.encode('utf-8'))
        fixed.append((f, lf - crlf))
print(f'① 统一 CRLF：{len(fixed)} 个文件（裸 LF 数）')
for f, n in fixed[:50]:
    print(f'    {f}: {n} 个裸 LF')

# 复验
bad = [f for f in os.listdir(ST) if f.endswith('.txt') and
       open(os.path.join(ST, f), 'rb').read().count(b'\n') !=
       open(os.path.join(ST, f), 'rb').read().count(b'\r\n')]
print(f'   复验：仍非纯 CRLF 的州文件 {len(bad)} {bad[:5]}')

# ② 解析器容错
P = os.path.join(ROOT, 'gamma_state_edits.py')
t = open(P, encoding='utf-8').read()
subs = [
    (r"re.search(r'provinces = \{\\r\\n\\t\\t([^\\r\\n]*)\\r\\n\\t\\}', t)",
     r"re.search(r'provinces = \{\r?\n\t\t([^\r\n]*)\r?\n\t\}', t)"),
    (r"re.sub(r'(provinces = \{\\r\\n\\t\\t)[^\\r\\n]*(\\r\\n\\t\\})',",
     r"re.sub(r'(provinces = \{\r?\n\t\t)[^\r\n]*(\r?\n\t\})',"),
]
n = 0
for old, new in subs:
    if old in t:
        t = t.replace(old, new)
        n += 1
open(P, 'w', encoding='utf-8').write(t)
import py_compile
py_compile.compile(P, doraise=True)
print(f'② gamma_state_edits.py 容错替换 {n} 处，编译 OK')

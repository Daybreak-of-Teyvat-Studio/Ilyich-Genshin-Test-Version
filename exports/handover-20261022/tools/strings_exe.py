# -*- coding: utf-8 -*-
"""strings_exe.py —— 提取 Hoi4ICU.exe 的可读字符串线索"""
import re, sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'F:\mod制作\Hoi4ICU.exe'
raw = open(P, 'rb').read()
print('文件大小:', len(raw))

# ASCII 串（>=6 字符）
strs = re.findall(rb'[\x20-\x7e]{6,}', raw)
pats = ['PyInstaller', 'python', 'electron', 'PyQt', 'PySide', 'tkinter', 'Nuitka',
        'hoi4', 'HOI4', 'Hearts', 'paradox', 'Paradox', 'steam', 'Steam',
        'launch', 'Launch', 'debug', 'checksum', 'mod', 'MOD', '.exe',
        'http', 'github', 'gitee', 'qq.com', 'lanzou', 'bilibili']
hits = {}
for s in strs:
    t = s.decode('latin1')
    for p in pats:
        if p in t and len(hits) < 400:
            hits.setdefault(p, set()).add(t[:120])
for p in pats:
    if p in hits:
        print(f'\n--- {p} ---')
        for v in list(hits[p])[:12]:
            print('  ', v)

# UTF-16 中文串
u16 = re.findall(rb'(?:[\x20-\x7e\u4e00-\u9fff]\x00){4,}', raw[:8*1024*1024])
cn = []
for s in u16:
    try:
        t = s.decode('utf-16-le')
    except Exception:
        continue
    if any('\u4e00' <= c <= '\u9fff' for c in t):
        cn.append(t)
print(f'\nUTF-16 中文串 {len(cn)} 条，样例（前 30）：')
seen = set()
for t in cn:
    t2 = t.strip()
    if t2 and t2 not in seen:
        seen.add(t2)
        print('  ', t2[:100])
    if len(seen) >= 30:
        break

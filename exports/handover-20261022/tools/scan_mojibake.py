# -*- coding: utf-8 -*-
"""scan_mojibake.py —— 全 mod 扫描 U+FFFD(替换字符)/锟斤拷 等坏字符"""
import os, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

# U+FFFD 的 UTF-8 字节序列 EF BF BD；以及常见乱码串
PATTERNS = [b'\xef\xbf\xbd', '\u951f\u65a4\u62f7'.encode('utf-8'), '\u951f\u5385'.encode('utf-8')]

hits = []
for dp, dn, fn in os.walk(G):
    dn[:] = [d for d in dn if d not in ('.backups', '.backup', '__pycache__')]
    for f in fn:
        if not f.endswith(('.txt', '.yml')):
            continue
        p = os.path.join(dp, f)
        raw = open(p, 'rb').read()
        for pat in PATTERNS:
            if pat in raw:
                n = raw.count(pat)
                hits.append((os.path.relpath(p, G), n))
                break
print(f'含坏字符的文件: {len(hits)}')
for h in hits[:40]:
    print(f'  {h[0]}: {h[1]} 处')

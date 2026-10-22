# -*- coding: utf-8 -*-
"""pri_bytes.py —— PRI 第 66 行原始字节与码点"""
import sys

sys.stdout.reconfigure(encoding='utf-8')
p = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\history\units\PRI_1936_Naval.txt'
raw = open(p, 'rb').read()
lines = raw.split(b'\r\n')
b = lines[65]
print('第 66 行字节数:', len(b))
print('前 100 字节 hex:', b[:100].hex())
s = b.decode('utf-8-sig', errors='replace')
print('前 80 字符码点:', ' '.join(f'{ord(c):04X}' for c in s[:80]))
print('前 80 字符:', s[:80])

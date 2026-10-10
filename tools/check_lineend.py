# -*- coding: utf-8 -*-
"""check_lineend.py —— 检查/修复 DOT_on_actions 的 BOM 与行尾"""
import os, glob, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
bd = sorted(glob.glob(os.path.join(ROOT, '.backups', 'equipfix_*')))[-1]
b = open(os.path.join(bd, 'DOT_on_actions.txt'), 'rb').read()
cur = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'common', 'on_actions', 'DOT_on_actions.txt')
r = open(cur, 'rb').read()
print('备份: BOM=', b[:3] == b'\xef\xbb\xbf', 'CRLF=', b.count(b'\r\n'), 'LF总=', b.count(b'\n'))
print('当前: BOM=', r[:3] == b'\xef\xbb\xbf', 'CRLF=', r.count(b'\r\n'), 'LF总=', r.count(b'\n'))

# 修复：恢复备份的 BOM 状态；行尾统一 CRLF（若备份为 CRLF）
want_bom = b[:3] == b'\xef\xbb\xbf'
want_crlf = b.count(b'\r\n') > b.count(b'\n') // 2
t = r
if t[:3] == b'\xef\xbb\xbf':
    t = t[3:]
t = t.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') if want_crlf else t
if want_bom:
    t = b'\xef\xbb\xbf' + t
open(cur, 'wb').write(t)
r2 = open(cur, 'rb').read()
print('修复后: BOM=', r2[:3] == b'\xef\xbb\xbf', 'CRLF=', r2.count(b'\r\n'), 'LF总=', r2.count(b'\n'))
print('内容等价(去BOM/行尾):', r2.replace(b'\r\n', b'\n').replace(b'\xef\xbb\xbf', b'') ==
      b.replace(b'\r\n', b'\n').replace(b'\xef\xbb\xbf', b'') or '注意：内容有差异（闲云机修复本身）')

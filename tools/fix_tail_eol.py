# -*- coding: utf-8 -*-
"""fix_tail_eol.py —— 检查并修复 buildings.txt 结尾换行（对齐原始/原版样貌）"""
import os, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

def tail_show(p, tag):
    raw = open(p, 'rb').read()
    print(f'  [{tag}] 末尾 60 字节: {raw[-60:]!r}')

print('=== 结尾字节对比 ===')
tail_show(os.path.join(V, 'map', 'buildings.txt'), 'vanilla')
tail_show(os.path.join(B, 'map', 'buildings.txt'), 'beta')
# 我们修复前的备份
bks = sorted(glob.glob(os.path.join(ROOT, '.backups', 'mapfix2_*', '仓库_buildings.txt')))
if bks:
    tail_show(bks[-1], '备份(修复前)')
tail_show(os.path.join(G, 'map', 'buildings.txt'), 'gamma当前(仓库)')
tail_show(os.path.join(D, 'map', 'buildings.txt'), 'gamma当前(副本)')

# 修复：去掉结尾多余空行（以最后一个非空行为文件结尾，不加尾换行——对齐备份样貌）
APPLY = '--apply' in sys.argv
print()
print('=== 修复（--apply 生效）===')
for tag, base in (('仓库', G), ('副本', D)):
    p = os.path.join(base, 'map', 'buildings.txt')
    raw = open(p, 'rb').read()
    fixed = raw.rstrip(b'\r\n') + b'\r\n'
    # 目标：最后一行内容后跟单个 \r\n 还是不加？先看备份：由上面的打印决定；这里统一用"最后一个非空行 + \r\n"的规范做法但去掉多余
    if raw.endswith(b'\r\n\r\n'):
        fixed = raw[:-2]
    elif not raw.endswith(b'\r\n'):
        fixed = raw + b'\r\n'
    else:
        # 单个 \r\n 结尾 —— 若是引擎仍报，则去掉尾换行
        fixed = raw.rstrip(b'\r\n')
    print(f'  {tag}: 现结尾 {raw[-8:]!r} -> 新结尾 {fixed[-8:]!r}')
    if APPLY:
        open(p, 'wb').write(fixed)
print(f'模式: {"已应用" if APPLY else "DRY"}')

# -*- coding: utf-8 -*-
"""find_was_numbers.py —— 反查 710/730/731/736/737 的原号州（注释 # name="STATE_N"）"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

WANT = {710, 730, 731, 736, 737, 709, 716, 725}
print('=== 州文件注释中的 # name="STATE_N" 反问映射 ===')
for f in sorted(glob.glob(os.path.join(G, 'history', 'states', '*.txt'))):
    head = open(f, encoding='utf-8-sig', errors='replace').read()[:400]
    m = re.search(r'name="DOT_STATE_(\d+)"\s*#\s*name="STATE_(\d+)"', head)
    if m:
        cur, was = int(m.group(1)), int(m.group(2))
        if was in WANT:
            t = open(f, encoding='utf-8-sig', errors='replace').read()
            ow = re.search(r'(?m)^\s*owner\s*=\s*(\w+)', t)
            print(f'  STATE_{was} → 现在是 DOT_STATE_{cur} (owner={ow.group(1) if ow else "-"})   [{os.path.basename(f)}]')

# 全部含注释的州（供参考的完整列表）
print()
print('=== 完整注释映射表（所有带 # name=STATE_N 的州）===')
rows = []
for f in sorted(glob.glob(os.path.join(G, 'history', 'states', '*.txt'))):
    head = open(f, encoding='utf-8-sig', errors='replace').read()[:400]
    m = re.search(r'name="DOT_STATE_(\d+)"\s*#\s*name="STATE_(\d+)"', head)
    if m:
        rows.append((int(m.group(2)), int(m.group(1))))
rows.sort()
print(f'  共 {len(rows)} 个:')
print('  ' + '  '.join(f'{was}→{cur}' for was, cur in rows))

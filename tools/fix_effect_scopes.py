# -*- coding: utf-8 -*-
"""fix_effect_scopes.py —— 将 DOT_Resources 决策的效果块号对齐到目标州号（DRY 默认，--apply 应用）"""
import os, re, sys, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'effect_scopes_{stamp}')
os.makedirs(BD, exist_ok=True)

REL = os.path.join('common', 'decisions', 'DOT_Resources.txt')

# 逐决策块处理：把块内"裸作用域 N = {"行对齐到 owns_state 的号
DEC_START = re.compile(r'^\s*(DOT_\w+)\s*=\s*\{')
SCOPE_LINE = re.compile(r'^(\s*)(\d+)(\s*=\s*\{)')
OWNS = re.compile(r'owns_state\s*=\s*(\d+)')

for tag, base in COPIES:
    p = os.path.join(base, REL)
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    ls = t.split('\n')
    # 找决策块范围
    starts = [(i, m.group(1)) for i, l in enumerate(ls) for m in [DEC_START.match(l)] if m]
    changes = []
    for idx, (si, name) in enumerate(starts):
        if name == 'DOT_Search_Resources':
            continue
        ei = starts[idx + 1][0] if idx + 1 < len(starts) else len(ls)
        blk = ls[si:ei]
        own = None
        for l in blk:
            m = OWNS.search(l)
            if m:
                own = m.group(1)
                break
        if not own:
            continue
        for j, l in enumerate(blk):
            m = SCOPE_LINE.match(l)
            if m and m.group(2) != own:
                changes.append((si + j + 1, name, m.group(2), own, l.strip()[:80]))
                ls[si + j] = m.group(1) + own + m.group(3)
    print(f'=== {tag}: {len(changes)} 处效果块号对齐 ===')
    for ln, name, old, new, ctx in changes:
        print(f'  L{ln} [{name[:36]}] {old} → {new}   ({ctx})')
    if APPLY and changes:
        shutil.copy2(p, os.path.join(BD, f'{tag}_DOT_Resources.txt'))
        open(p, 'wb').write(('\n'.join(ls)).encode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'))
print(f'模式: {"已应用" if APPLY else "DRY"}  备份: {BD}')

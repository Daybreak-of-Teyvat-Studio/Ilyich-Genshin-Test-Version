# -*- coding: utf-8 -*-
"""delete_sea_states.py —— 删除全部 41 个海州 + 迁移残留引用（DRY 默认，--apply 应用）
A) 引用迁移（按州文件注释的原号全表）：
   730→301（天空岛：DOT_Space_Program + ABY_Event）；731→300（VAN×2）；
   710→583（ANR + LYY）；852→695、736→294（INA_Focus prioritize）
B) 删除 41 个海州文件（709-717、719-750）
C) 清理 airports.txt/rocketsites.txt 的海州行
"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'del_sea_{stamp}')
os.makedirs(BD, exist_ok=True)

SEA = set(range(709, 718)) | set(range(719, 751))

# ===== A) 引用迁移 =====
EDITS = [
    (os.path.join('common', 'decisions', 'DOT_Space_Program_decisions.txt'),
     [('730 = { is_controlled_by = ROOT }', '301 = { is_controlled_by = ROOT }')]),
    (os.path.join('events', 'ABY_Event.txt'),
     [('730 = { is_controlled_by = ROOT }', '301 = { is_controlled_by = ROOT }')]),
    (os.path.join('common', 'decisions', 'VAN_decisions.txt'),
     [('state = 731', 'state = 300')]),
    (os.path.join('common', 'scripted_triggers', 'VAN_scripted_triggers.txt'),
     [('state = 731', 'state = 300')]),
    (os.path.join('common', 'national_focus', 'INA_Focus.txt'),
     [('prioritize = { 852 736 }', 'prioritize = { 695 294 }')]),
    (os.path.join('common', 'on_actions', 'ANR_influence_on_actions.txt'),
     [('FROM.FROM = { state = 710 }', 'FROM.FROM = { state = 583 }')]),
    (os.path.join('common', 'scripted_effects', 'LYY_scripted_effects.txt'),
     [('transfer_state = 710', 'transfer_state = 583')]),
]
print('=== A) 引用迁移 ===')
for tag, base in COPIES:
    for rel, subs in EDITS:
        p = os.path.join(base, rel)
        raw = open(p, 'rb').read()
        t = raw.decode('utf-8-sig')
        for old, new in subs:
            n = t.count(old)
            if n != 1:
                print(f'  {tag} {rel}: ★ "{old[:40]}" ×{n}（预期 1）——跳过该替换')
                continue
            t = t.replace(old, new)
            print(f'  {tag} {os.path.basename(rel)}: {old[:40]} → {new[:40]} ✓')
        if APPLY:
            shutil.copy2(p, os.path.join(BD, f'{tag}_{os.path.basename(p)}'))
            open(p, 'wb').write(t.encode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'))

# ===== B) 删除海州文件 =====
print()
print('=== B) 删除 41 个海州文件 ===')
for tag, base in COPIES:
    d = os.path.join(base, 'history', 'states')
    victims = []
    for f in glob.glob(os.path.join(d, '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
        if m and int(m.group(1)) in SEA:
            victims.append(f)
    print(f'  {tag}: 找到 {len(victims)} 个（预期 41）')
    if APPLY:
        bd = os.path.join(BD, tag + '_states')
        os.makedirs(bd, exist_ok=True)
        for f in victims:
            shutil.copy2(f, os.path.join(bd, os.path.basename(f)))
            os.remove(f)
        print(f'  {tag}: 已删除并备份到 {bd}')

# ===== C) 清理 airports/rocketsites =====
print()
print('=== C) 清理 airports.txt / rocketsites.txt 海州行 ===')
for tag, base in COPIES:
    for fname in ('airports.txt', 'rocketsites.txt'):
        p = os.path.join(base, 'map', fname)
        raw = open(p, 'rb').read()
        t = raw.decode('utf-8-sig')
        lines = t.split('\n')
        keep = [l for l in lines if l.strip() and not (re.match(r'\s*(\d+)\s*=', l) and int(re.match(r'\s*(\d+)', l).group(1)) in SEA)]
        dropped = len([l for l in lines if l.strip()]) - len(keep)
        print(f'  {tag} {fname}: 移除 {dropped} 行, 剩 {len(keep)} 行')
        if APPLY:
            shutil.copy2(p, os.path.join(BD, f'{tag}_{fname}'))
            open(p, 'wb').write(('\r\n'.join(keep) + '\r\n').encode('utf-8'))

# ===== 验证 =====
if APPLY:
    print()
    print('=== 验证 ===')
    for tag, base in COPIES:
        n = len(glob.glob(os.path.join(base, 'history', 'states', '*.txt')))
        sea_left = 0
        for f in glob.glob(os.path.join(base, 'history', 'states', '*.txt')):
            m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', open(f, encoding='utf-8-sig', errors='replace').read())
            if m and int(m.group(1)) in SEA:
                sea_left += 1
        ap = len([l for l in open(os.path.join(base, 'map', 'airports.txt'), encoding='utf-8-sig', errors='replace') if l.strip()])
        print(f'  {tag}: 州文件 {n} 个（预期 709）, 残留海州 {sea_left}（预期 0）, airports {ap} 行（预期 709）')
print(f'模式: {"已应用" if APPLY else "DRY"}  备份: {BD}')

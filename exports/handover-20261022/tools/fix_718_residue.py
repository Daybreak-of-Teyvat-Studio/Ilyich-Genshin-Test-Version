# -*- coding: utf-8 -*-
"""fix_718_residue.py —— 718→709 重编号的残留引用清理（DRY 默认，--apply 应用）
A) NCE 首都: capital = 718 → 709（悬空首都！）
B) airports.txt / rocketsites.txt: 718={...} → 709={...}（选址表随州号）
C) 709 州文件 name 键: DOT_STATE_718 → DOT_STATE_709（拆包一致）
D) loc: DOT_STATE_709 = "回声之子"（活键）；DOT_STATE_718 → "*"（死键）
E) 只读：全树 state 语法引用 710-750 复查（应为 0，除省份/坐标噪音）
"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'fix718_{stamp}')
os.makedirs(BD, exist_ok=True)

def edit(p, subs, tag, label):
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    ok = True
    for old, new, expect in subs:
        n = t.count(old)
        if n != expect:
            print(f'  {tag} {label}: ★ "{old[:50]}" ×{n}（预期 {expect}）—— 跳过')
            ok = False
    if not ok:
        return
    for old, new, expect in subs:
        t = t.replace(old, new)
        print(f'  {tag} {label}: {old[:60]} → {new[:60]} ✓')
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_{os.path.basename(p)}'))
        open(p, 'wb').write(t.encode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'))

print('=== A) NCE 首都 ===')
for tag, base in COPIES:
    edit(os.path.join(base, 'history', 'countries', 'NCE - Children_of_Echoes.txt'),
         [('capital = 718', 'capital = 709', 1)], tag, 'NCE首都')

print()
print('=== B) airports / rocketsites ===')
for tag, base in COPIES:
    for fname in ('airports.txt', 'rocketsites.txt'):
        edit(os.path.join(base, 'map', fname),
             [('718={', '709={', 1)], tag, fname)

print()
print('=== C) 709 州文件 name 键 ===')
for tag, base in COPIES:
    edit(os.path.join(base, 'history', 'states', '709-State_709.txt'),
         [('name="DOT_STATE_718" # name="STATE_709"', 'name="DOT_STATE_709" # name="STATE_709"', 1)],
         tag, '709州文件')

print()
print('=== D) loc 键 ===')
LOC = os.path.join('localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
for tag, base in COPIES:
    edit(os.path.join(base, LOC),
         [('DOT_STATE_709:0 "*"', 'DOT_STATE_709:0 "回声之子"', 1),
          ('DOT_STATE_718:0 "回声之子"', 'DOT_STATE_718:0 "*"', 1)],
         tag, 'loc')

print()
print('=== E) 只读：state 语法引用 710-750 复查 ===')
PAT = re.compile(r'((?:state|owns_state|controls_state|transfer_state|state_id|capital)\s*=\s*)(7[1-4]\d|750)(?!\d)')
for tag, base in (('仓库', COPIES[0][1]),):
    for sub in ('common', 'events', 'history'):
        for dirpath, dirnames, filenames in os.walk(os.path.join(base, sub)):
            if 'states' in dirpath.split(os.sep):
                continue
            for fn in filenames:
                if not fn.endswith('.txt'):
                    continue
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, base)
                if 'resource_prospecting' in rel or '14_sea' in rel or '12_wuw' in rel:
                    continue
                t = open(fp, encoding='utf-8-sig', errors='replace').read()
                for i, l in enumerate(t.split('\n')):
                    for m in PAT.finditer(l):
                        print(f'  {rel} L{i+1}: {l.strip()[:130]}')
    print('  （无输出 = 干净）')

if APPLY:
    print()
    print('=== 验证 ===')
    for tag, base in COPIES:
        t = open(os.path.join(base, 'history', 'states', '709-State_709.txt'), encoding='utf-8-sig', errors='replace').read()
        n1 = 'name="DOT_STATE_709"' in t and 'id = 709' in t
        n2 = 'capital = 709' in open(os.path.join(base, 'history', 'countries', 'NCE - Children_of_Echoes.txt'), encoding='utf-8-sig', errors='replace').read()
        ap = open(os.path.join(base, 'map', 'airports.txt'), encoding='utf-8-sig', errors='replace').read()
        n3 = bool(re.search(r'(?m)^\s*709\s*=', ap)) and not bool(re.search(r'(?m)^\s*718\s*=', ap))
        lp = open(os.path.join(base, LOC), encoding='utf-8-sig', errors='replace').read()
        n4 = 'DOT_STATE_709:0 "回声之子"' in lp
        print(f'  {tag}: 州文件正确={n1} 首都={n2} airports709键={n3} loc={n4}')
print(f'模式: {"已应用" if APPLY else "DRY"}  备份: {BD}')

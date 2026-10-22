# -*- coding: utf-8 -*-
"""names_refs_fix.py —— 六名字转移陆地州 + 740 脚本引用→570（DRY 默认，--apply 应用）
A) loc：740/741/744/745/747/748 六键 → "*"；570 键 → "知比山"（字节级，保 BOM/CRLF）
B) 脚本：state 语法引用 740 → 570（8 个文件；逐一打印改动）
C) 只读报告：741/744/745/747/748 的脚本引用（应为 0）+ 剩余的 710/731/736 引用清单
"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
COPIES = [('仓库', G), ('副本', D)]
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'names_refs_{stamp}')
os.makedirs(BD, exist_ok=True)

# ============ A) loc 六键 ============
LOC_REL = os.path.join('localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
SEA_CLEAR = [('DOT_STATE_740:0 "知比山"', 'DOT_STATE_740:0 "*"'),
             ('DOT_STATE_741:0 "茂知祭场"', 'DOT_STATE_741:0 "*"'),
             ('DOT_STATE_744:0 "天云峠"', 'DOT_STATE_744:0 "*"'),
             ('DOT_STATE_745:0 "无想刃狭间"', 'DOT_STATE_745:0 "*"'),
             ('DOT_STATE_747:0 "蛇骨矿洞"', 'DOT_STATE_747:0 "*"'),
             ('DOT_STATE_748:0 "望泷村"', 'DOT_STATE_748:0 "*"'),
             ('DOT_STATE_570:0 "*"', 'DOT_STATE_570:0 "知比山"')]
print('=' * 62)
print('【A】loc：六名字转移（海州键清空 + 570 命名）')
for tag, base in COPIES:
    p = os.path.join(base, LOC_REL)
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    ok = True
    for old, new in SEA_CLEAR:
        n = t.count(old)
        if n != 1:
            print(f'  {tag}: ★"{old[:30]}" 匹配 {n} 次（应 1）')
            ok = False
    if not ok:
        continue
    t2 = t
    for old, new in SEA_CLEAR:
        print(f'  {tag}: {old}  →  {new}')
        t2 = t2.replace(old, new)
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_state_names_gamma.yml'))
        open(p, 'wb').write(t2.encode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'))

# ============ B) 脚本 740→570 ============
print()
print('=' * 62)
print('【B】脚本引用 740 → 570')
RX = re.compile(r'((?:state|owns_state|controls_state|transfer_state)\s*=\s*)740(?!\d)')
FILES = ['common\\decisions\\DOT_Resources.txt', 'common\\decisions\\KNA_decision.txt',
         'common\\decisions\\VAN_decisions.txt', 'common\\ideas\\DRA_andrius_manufacture.txt',
         'common\\national_focus\\FAV_FocusTree_00.txt', 'common\\national_focus\\FAV_FocusTree_01.txt',
         'common\\national_focus\\LAW_FocusTree_02.txt', 'common\\national_focus\\NewMOT_FocusTree_00.txt',
         'common\\on_actions\\ANR_influence_on_actions.txt',
         'common\\scripted_triggers\\VAN_scripted_triggers.txt']
for tag, base in COPIES:
    total = 0
    for rel in FILES:
        p = os.path.join(base, *rel.split('\\'))
        raw = open(p, 'rb').read()
        t = raw.decode('utf-8-sig')
        hits = list(RX.finditer(t))
        if not hits:
            continue
        for m in hits:
            ln = t[:m.start()].count('\n') + 1
            print(f'  {tag} {rel} L{ln}: ...{t[max(0,m.start()-55):m.end()+25].strip()[:110]}')
        total += len(hits)
        if APPLY:
            shutil.copy2(p, os.path.join(BD, f'{tag}_{os.path.basename(p)}'))
            t2 = RX.sub(r'\g<1>570', t)
            open(p, 'wb').write(t2.encode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'))
    print(f'  {tag}: 共改 {total} 处')

# ============ C) 只读报告 ============
print()
print('=' * 62)
print('【C】剩余引用清单（只读）')
RX2 = re.compile(r'((?:state|owns_state|controls_state|transfer_state)\s*=\s*)(741|744|745|747|748|710|731|736|737|716|725)(?!\d)')
for tag, base in (('仓库', G),):
    for sub in ('common', 'events'):
        for dirpath, dirnames, filenames in os.walk(os.path.join(base, sub)):
            for fn in filenames:
                if not fn.endswith('.txt'):
                    continue
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, base)
                if 'resource_prospecting' in rel:
                    continue  # 原版残留
                t = open(fp, encoding='utf-8-sig', errors='replace').read()
                for m in RX2.finditer(t):
                    ln = t[:m.start()].count('\n') + 1
                    print(f'  {rel} L{ln}: [{m.group(2)}] ...{t[max(0,m.start()-50):m.end()+20].strip()[:100]}')
print(f'模式: {"已应用" if APPLY else "DRY"}  备份: {BD}')

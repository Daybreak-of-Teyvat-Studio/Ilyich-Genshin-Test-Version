# -*- coding: utf-8 -*-
"""batch_013_fix.py —— ①浪船 372→269 ②VP4219 去重 ③281/256 命名（DRY 默认，--apply 应用）"""
import os, re, sys, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
APPLY = '--apply' in sys.argv
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'batch013_{stamp}')
os.makedirs(BD, exist_ok=True)

def edit_re(p, pattern, repl, expect, tag, label, regex=True):
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    if regex:
        pat = re.compile(pattern)
        n = len(pat.findall(t))
    else:
        n = t.count(pattern)
    if n != expect:
        print(f'  {tag} {label}: ★ 匹配 {n} 次（预期 {expect}）—— 跳过')
        return
    t2 = re.sub(pattern, repl, t) if regex else t.replace(pattern, repl)
    if APPLY:
        shutil.copy2(p, os.path.join(BD, f'{tag}_{os.path.basename(p)}'))
        open(p, 'wb').write(t2.encode('utf-8-sig' if raw[:3] == b'\xef\xbb\xbf' else 'utf-8'))
    print(f'  {tag} {label}: ×{n} ✓' + ('' if APPLY else ' (DRY)'))

print('=== ① 浪船决策 372→269（3 处）===')
for tag, base in COPIES:
    p = os.path.join(base, 'common', 'decisions', 'SUM_decisions.txt')
    edit_re(p, r'(?m)^(\s*)372(\s*=\s*\{)', r'\g<1>269\g<2>', 3, tag, 'SUM浪船')

print()
print('=== ② VP4219 去重 ===')
for tag, base in COPIES:
    p = os.path.join(base, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml')
    edit_re(p, 'VICTORY_POINTS_4219:0 "特菈佐莉特拉佐莉的铸造工坊"',
            'VICTORY_POINTS_4219:0 "特拉佐莉的铸造工坊"', 1, tag, 'VP4219', regex=False)

print()
print('=== ③ 281/256 命名 ===')
for tag, base in COPIES:
    p = os.path.join(base, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
    edit_re(p, 'DOT_STATE_281:0 "焰羽谷"', 'DOT_STATE_281:0 "生栖树沼"', 1, tag, '281命名', regex=False)
    edit_re(p, 'DOT_STATE_256:0 "*"', 'DOT_STATE_256:0 "奥古洛夫镇"', 1, tag, '256命名', regex=False)

if APPLY:
    print()
    print('=== 验证 ===')
    for tag, base in COPIES:
        sd = open(os.path.join(base, 'common', 'decisions', 'SUM_decisions.txt'), encoding='utf-8-sig', errors='replace').read()
        vp = open(os.path.join(base, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml'), encoding='utf-8-sig', errors='replace').read()
        nm = open(os.path.join(base, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml'), encoding='utf-8-sig', errors='replace').read()
        c1 = len(re.findall(r'(?m)^\s*269\s*=\s*\{', sd))
        print(f'  {tag}: 浪船269引用×{c1} | VP4219={ "特拉佐莉的铸造工坊" in vp } | 281={ "DOT_STATE_281:0 \"生栖树沼\"" in nm } | 256={ "DOT_STATE_256:0 \"奥古洛夫镇\"" in nm }')
print(f'模式: {"已应用" if APPLY else "DRY"}  备份: {BD}')

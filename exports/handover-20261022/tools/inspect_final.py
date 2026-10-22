# -*- coding: utf-8 -*-
"""inspect_final.py —— 只读核对：708↔750 换位后的两边状态一致性"""
import os, re, sys, hashlib

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DEP = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
SKIP = {'.backups', '.backup', '__pycache__'}

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()

print('=== 关键文件逐项 ===')
checks = [
    'history/states/708-State_708.txt',
    'history/states/750-State_750.txt',
    'localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml',
    'map/buildings.txt',
    'common/decisions/KNA_decision.txt',
    'common/national_focus/INA_Focus.txt',
    'history/countries/NCE - Children_of_Echoes.txt',
    'history/countries/NAT - Natlan.txt',
]
for rel in checks:
    rp = os.path.join(REPO, *rel.split('/'))
    dp = os.path.join(DEP, *rel.split('/'))
    r_ok, d_ok = os.path.exists(rp), os.path.exists(dp)
    same = (md5(rp) == md5(dp)) if (r_ok and d_ok) else None
    print(f'  {rel}: 仓库{"有" if r_ok else "无"} 副本{"有" if d_ok else "无"} 一致={"✓" if same else ("✗" if same is False else "-")}')

print()
print('=== 状态详情（两边）===')
for tag, base in (('仓库', REPO), ('副本', DEP)):
    ST = os.path.join(base, 'history', 'states')
    for sid in (708, 750):
        t = open(os.path.join(ST, f'{sid}-State_{sid}.txt'), encoding='utf-8-sig', errors='replace').read()
        om = re.search(r'\bowner\s*=\s*(\w+)', t)
        pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        provs = pm.group(1).split() if pm else []
        print(f'  {tag} s{sid}: owner={om.group(1) if om else "无"} 省数={len(provs)} 首省={provs[0] if provs else "-"}')
    loc = open(os.path.join(base, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml'),
               encoding='utf-8-sig', errors='replace').read()
    for k in (708, 750):
        mm = re.search(rf'DOT_STATE_{k}:0\s*"([^"]*)"', loc)
        print(f'  {tag} DOT_STATE_{k} = "{mm.group(1) if mm else "无"}"')
    bp = open(os.path.join(base, 'map', 'buildings.txt'), 'rb').read().decode('utf-8-sig')
    c = sum(1 for l in bp.split('\r\n') if l.split(';')[:1] and l.split(';')[0] in ('708', '750'))
    c708 = sum(1 for l in bp.split('\r\n') if l.split(';')[0] == '708')
    c750 = sum(1 for l in bp.split('\r\n') if l.split(';')[0] == '750')
    print(f'  {tag} buildings: 708行={c708} 750行={c750}')
    # NCE 首都
    nt = open(os.path.join(base, 'history', 'countries', 'NCE - Children_of_Echoes.txt'),
              encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*capital\s*=\s*(\d+)', nt)
    print(f'  {tag} NCE capital={m.group(1)}')

print()
print('=== 全树差异 ===')
def tree(base):
    out = {}
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, base)] = md5(p)
    return out
tr, td = tree(REPO), tree(DEP)
diff = sorted(k for k in set(tr) & set(td) if tr[k] != td[k])
print(f'内容不同 {len(diff)}: {diff[:15]}')
print(f'只在仓库 {len(set(tr)-set(td))}，只在副本 {len(set(td)-set(tr))}')

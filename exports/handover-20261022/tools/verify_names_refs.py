# -*- coding: utf-8 -*-
"""verify_names_refs.py —— 回读验证：loc 七键 + 脚本 740 已改 570 / 731、710 未动"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
D = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

LOC = os.path.join('localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
for tag, base in (('仓库', G), ('副本', D)):
    print(f'=== {tag} ===')
    raw = open(os.path.join(base, LOC), 'rb').read()
    t = raw.decode('utf-8-sig')
    for sid in (740, 741, 744, 745, 747, 748, 570, 136, 254, 574, 636, 695):
        m = re.search(rf'(?m)^\s*DOT_STATE_{sid}\s*:\s*\d*\s*"([^"]*)"', t)
        print(f'  DOT_STATE_{sid} = {m.group(1) if m else "★无键"}')
    # 六个名字在全文的残留
    for nm in ('知比山', '茂知祭场', '天云峠', '无想刃狭间', '蛇骨矿洞', '望泷村'):
        keys = [m.group(1) for m in re.finditer(rf'(?m)^\s*DOT_STATE_(\d+)\s*:\s*\d*\s*"{nm}"', t)]
        print(f'  "{nm}" 现存于 DOT_STATE: {keys}')
    # 脚本抽检
    p = os.path.join(base, 'common', 'decisions', 'DOT_Resources.txt')
    tt = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'  DOT_Resources: state = 740 剩 {len(re.findall(r"state =s*=s*740(?![0-9])".replace("s*","\\s*"), tt))} 处, state = 570 出现 {tt.count("state = 570")} 处')
    p = os.path.join(base, 'common', 'scripted_triggers', 'VAN_scripted_triggers.txt')
    tt = open(p, encoding='utf-8-sig', errors='replace').read()
    print(f'  VAN_triggers: "state = 740"剩 {tt.count("state = 740")}  |  "state = 570"出 {tt.count("state = 570")}  |  "state = 731"剩 {tt.count("state = 731")} (应保留)')
    print()

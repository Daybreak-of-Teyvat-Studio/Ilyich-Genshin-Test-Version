# -*- coding: utf-8 -*-
"""修 idea 小图标模板：用原版 spirit_idea_entry_small 块替换 mod 的（双副本）"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
rel = os.path.join('interface', 'frontendgamesetupview.gui')
o = []

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
if r.stdout.strip() != '0':
    print('hoi4 运行中，跳过')
    sys.exit(0)

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig', errors='replace')

def close_brace(t, start):
    depth = 0; k = start
    while k < len(t):
        if t[k] == '{': depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0: return k + 1
        k += 1
    return -1

def named_block(t, name):
    m = re.search(r'name\s*=\s*"' + re.escape(name) + r'"', t)
    if not m: return None, None
    start = None
    for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
        start = m2
    bs = t.index('{', start.start())
    be = close_brace(t, bs)
    ls = t.rfind('\n', 0, start.start()) + 1
    return t[ls:be], (ls, be)

vb, _ = named_block(rd(os.path.join(V, 'interface', 'frontendgamesetupview.gui')), 'spirit_idea_entry_small')
o.append(f'原版块提取: {"成功" if vb else "失败"}')
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, rel)
    t = rd(fp)
    mb, span = named_block(t, 'spirit_idea_entry_small')
    if not mb or not span:
        o.append(f'{label}: 未找到 mod 块 ✗')
        continue
    t2 = t[:span[0]] + vb.rstrip() + t[span[1]:]
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    o.append(f'{label}: 已替换, {len(chk)}B, 括号 {chk.count("{")}=={chk.count("}")}')
    # 复读小图标参数
    i = chk.find('spirit_idea_entry_small')
    o.append('   新块: ' + ' '.join(chk[i:i+260].split())[:220])

a = io.open(os.path.join(REPO, rel), 'rb').read()
b = io.open(os.path.join(DEPL, rel), 'rb').read()
o.append(f'双副本一致: {a == b}')
print('\n'.join(o))

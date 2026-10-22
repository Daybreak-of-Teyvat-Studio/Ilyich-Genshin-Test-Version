# -*- coding: utf-8 -*-
"""配对修复：setup gui 补 filters 元素（原版块）+ bookmark 启用 filters（双副本）"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
o = []

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
if r.stdout.strip() != '0':
    print('hoi4 运行中，跳过')
    sys.exit(0)

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig', errors='replace')

def close_brace(t, s):
    d = 0; k = s
    while k < len(t):
        if t[k] == '{': d += 1
        elif t[k] == '}':
            d -= 1
            if d == 0: return k + 1
        k += 1
    return -1

def span_of(t, name):
    m = re.search(r'name\s*=\s*"' + re.escape(name) + r'"', t)
    if not m: return None
    st = None
    for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
        st = m2
    if st is None: return None
    bs = t.index('{', st.start())
    be = close_brace(t, bs)
    return (t.rfind('\n', 0, st.start()) + 1, be, t[st.start():be])

# 1) UI：原版 filters 元素 → 插到 mod 的 gamesetup_interesting_countries_window 内
tv = rd(os.path.join(V, 'interface', 'frontendgamesetupview.gui'))
vf = span_of(tv, 'filters')
o.append(f'原版 filters 块: {"成功" if vf else "失败"}')
blk = vf[2] if vf else None
win_name = 'gamesetup_interesting_countries_window'
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'frontendgamesetupview.gui')
    t = rd(fp)
    if re.search(r'name\s*=\s*"filters"', t):
        o.append(f'{label}: 已有 filters 元素 ✓')
        continue
    w = span_of(t, win_name)
    if not w:
        o.append(f'{label}: 未找到窗口 {win_name} ✗')
        continue
    ins = t.rfind('\n', 0, w[1] - 1) + 1
    t2 = t[:ins] + blk.rstrip() + '\n' + t[ins:]
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    o.append(f'{label}: filters 已插入窗口内, {len(chk)}B, 括号 {chk.count("{")}=={chk.count("}")}')

# 2) bookmark：filters 启用
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'common', 'bookmarks', '3_The_Traveler.txt')
    t = rd(fp)
    t2, n = re.subn(r'(?m)^[ \t]*#\s*filters\s*=\s*\{\s*new_content\s+continent\s*\}',
                    '\t\tfilters = { new_content continent }', t)
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    o.append(f'{label} bookmark: filters 启用 {n} 处, 括号 {chk.count("{")}=={chk.count("}")}')

for rel in (os.path.join('interface', 'frontendgamesetupview.gui'), os.path.join('common', 'bookmarks', '3_The_Traveler.txt')):
    a = io.open(os.path.join(REPO, rel), 'rb').read()
    b = io.open(os.path.join(DEPL, rel), 'rb').read()
    o.append(f'{rel}: 双副本一致={a == b}')
print('\n'.join(o))

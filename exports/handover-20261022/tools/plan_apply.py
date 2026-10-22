# -*- coding: utf-8 -*-
"""按方案：bookmark 加 filters；idea 小图标块 + ideas_grid 按原版替换（双副本）"""
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

# 1) bookmark：注释行 → 生效
rel_bm = os.path.join('common', 'bookmarks', '3_The_Traveler.txt')
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, rel_bm)
    t = rd(fp)
    t2, n = re.subn(r'(?m)^[ \t]*#\s*filters\s*=\s*\{\s*new_content\s+continent\s*\}',
                    '\t\tfilters = { new_content continent }', t)
    if n == 0:
        # 没有注释行则在 default 行后插入
        t2, n2 = re.subn(r'(?m)^(\t\tdefault = yes[ \t]*)$',
                         r'\g<1>\n\t\tfilters = { new_content continent }', t)
    else:
        n2 = 0
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    has = 'filters = { new_content continent }' in chk
    o.append(f'{label} bookmark: 注释改生效={n}, 插入={n2}, 现含 filters={has}, 括号 {chk.count("{")}=={chk.count("}")}')

# 2) idea 块：小图标 + ideas_grid 按原版替换
rel_gui = os.path.join('interface', 'frontendgamesetupview.gui')
tv = rd(os.path.join(V, 'interface', 'frontendgamesetupview.gui'))
v_small = span_of(tv, 'spirit_idea_entry_small')
v_grid = span_of(tv, 'ideas_grid')
o.append(f'原版块提取: small={"成功" if v_small else "失败"}, grid={"成功" if v_grid else "失败"}')
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, rel_gui)
    t = rd(fp)
    g_small = span_of(t, 'spirit_idea_entry_small')
    g_grid = span_of(t, 'ideas_grid')
    if not g_small or not g_grid:
        o.append(f'{label}: 未找到块 ✗')
        continue
    # 先替换靠后的（grid），再替换靠前的（small），避免位移
    if g_grid[0] > g_small[0]:
        t = t[:g_grid[0]] + v_grid[2].rstrip() + t[g_grid[1]:]
        t = t[:g_small[0]] + v_small[2].rstrip() + t[g_small[1]:]
    else:
        t = t[:g_small[0]] + v_small[2].rstrip() + t[g_small[1]:]
        b2 = span_of(t, 'ideas_grid')
        t = t[:b2[0]] + v_grid[2].rstrip() + t[b2[1]:]
    io.open(fp, 'wb').write(t.encode('utf-8'))
    chk = rd(fp)
    i = chk.find('spirit_idea_entry_small')
    j = chk.find('ideas_grid')
    o.append(f'{label} gui: {len(chk)}B, 括号 {chk.count("{")}=={chk.count("}")}')
    o.append('   small: ' + ' '.join(chk[i:i+200].split())[:160])
    o.append('   grid : ' + ' '.join(chk[j:j+200].split())[:160])

for rel in (rel_bm, rel_gui):
    a = io.open(os.path.join(REPO, rel), 'rb').read()
    b = io.open(os.path.join(DEPL, rel), 'rb').read()
    o.append(f'{rel}: 双副本一致={a == b}')
print('\n'.join(o))

# -*- coding: utf-8 -*-
"""bug3：core.gfx 补 'x' sprite（唯一缺失项），双副本（游戏未运行才写）"""
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

def close_brace(t, start):
    depth = 0; k = start
    while k < len(t):
        if t[k] == '{': depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0: return k + 1
        k += 1
    return -1

# 原版 x sprite 块 + 贴图检查
tv = rd(os.path.join(V, 'interface', 'core.gfx'))
m = re.search(r'name\s*=\s*"x"', tv)
start = None
for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', tv[:m.start()]):
    start = m2
bs = tv.index('{', start.start())
be = close_brace(tv, bs)
blk = tv[start.start():be]
tx = re.search(r'texturefile\s*=\s*"([^"]+)"', blk)
o.append(f'x sprite 块: {" ".join(blk.split())[:160]}')
o.append(f'贴图: {tx.group(1) if tx else "?"} 原版存在={os.path.exists(os.path.join(V, tx.group(1).replace("//", "/").lstrip("/"))) if tx else "?"}')

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'core.gfx')
    t = rd(fp)
    if re.search(r'name\s*=\s*"x"', t):
        o.append(f'{label}: 已含 x ✓')
        continue
    i = t.find('spriteTypes')
    bs2 = t.index('{', i)
    be2 = close_brace(t, bs2)
    ins = t.rfind('\n', 0, be2 - 1) + 1
    t2 = t[:ins] + blk + '\n\t' + t[ins:]
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    o.append(f'{label}: 已加 x sprite, {len(t2)}B, 括号 {chk.count("{")}=={chk.count("}")}')

a = io.open(os.path.join(REPO, 'interface', 'core.gfx'), 'rb').read()
b = io.open(os.path.join(DEPL, 'interface', 'core.gfx'), 'rb').read()
o.append(f'双副本一致: {a == b}')
print('\n'.join(o))

# -*- coding: utf-8 -*-
"""bug2：bookmark 主要国家顺序 → MOT, LYY, INA, SUM, FON, NAT, NDK, SNE（双副本）"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
rel = os.path.join('common', 'bookmarks', '3_The_Traveler.txt')
ORDER = ['INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
o = []

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
if r.stdout.strip() != '0':
    print('hoi4 运行中，跳过（等游戏退出）')
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

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, rel)
    t = rd(fp)
    # 定位 ROW 2 段
    i0 = t.find('### ROW 2 ###')
    i1 = t.find('#mini', i0)
    if i0 < 0 or i1 < 0:
        o.append(f'{label}: 未找到 ROW2 段 ✗')
        continue
    seg = t[i0:i1]
    # 拆块：每个块 = 可选前置注释 + "TAG" = { ... }
    blocks = {}
    pos = 0
    pat = re.compile(r'(?m)^([ \t]*(?:#[^\r\n]*[\r\n]+)?[ \t]*"[A-Z]{3}"\s*=\s*\{)')
    matches = list(pat.finditer(seg))
    o.append(f'{label} ROW2 内找到 {len(matches)} 个块')
    for j, m in enumerate(matches):
        tag = re.search(r'"([A-Z]{3})"', m.group(1)).group(1)
        bs = seg.index('{', m.start()) if False else None
        # 从匹配起点开始找块起始 '{'
        brace_pos = seg.index('{', m.start())
        be = close_brace(seg, brace_pos)
        blocks[tag] = seg[m.start():be]
    missing = [t2 for t2 in ORDER if t2 not in blocks]
    o.append(f'  缺失: {missing if missing else "无"}')
    if missing:
        continue
    newseg = '### ROW 2 ###\r\n\r\n' + '\r\n\r\n'.join(blocks[t2].rstrip() for t2 in ORDER) + '\r\n\r\n'
    t2 = t[:i0] + newseg + t[i1:]
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    seq = [x.group(1) for x in re.finditer(r'"([A-Z]{3})"\s*=\s*\{', chk)]
    o.append(f'  {label}: 现 tag 序列={seq}, 括号 {chk.count("{")}=={chk.count("}")}')

a = io.open(os.path.join(REPO, rel), 'rb').read()
b = io.open(os.path.join(DEPL, rel), 'rb').read()
o.append(f'双副本一致: {a == b}')
print('\n'.join(o))

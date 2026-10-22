# -*- coding: utf-8 -*-
"""实验：8 大国书签条目补 version = base_game（修 \r 陷阱）"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
MAJ = ['MOT', 'LYY', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
o = []

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
if r.stdout.strip() != '0':
    print('hoi4 运行中，跳过')
    sys.exit(0)

def close_brace(t, s):
    d = 0; k = s
    while k < len(t):
        if t[k] == '{': d += 1
        elif t[k] == '}':
            d -= 1
            if d == 0: return k + 1
        k += 1
    return -1

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'common', 'bookmarks', '3_The_Traveler.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    n = 0
    for tag in MAJ:
        m = re.search(r'(?m)^[ \t]*"?' + tag + r'"?\s*=\s*\{', t)
        if not m:
            continue
        bs = t.index('{', m.start())
        be = close_brace(t, bs)
        blk = t[bs:be]
        if re.search(r'(?m)^\s*version\s*=', blk):
            continue
        # 注释版去注释
        blk2, nn = re.subn(r'(?m)^([ \t]*)#[ \t]*version[ \t]*=[^\r\n]*',
                           r'\g<1>version = base_game', blk, count=1)
        if nn == 0:
            # 插到 ideology 行后
            blk2, nn = re.subn(r'(?m)^([ \t]*)ideology\s*=[^\r\n]*',
                               r'\g<0>\r\n\g<1>version = base_game', blk, count=1)
        if nn:
            t = t[:bs] + blk2 + t[be:]
            n += 1
    io.open(fp, 'wb').write(t.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    o.append(f'{label}: 补 version {n} 处, 文件含 {chk.count("version = base_game")} 处, 括号 {chk.count("{")}=={chk.count("}")}')
    # 抽看 MOT
    i = chk.find('MOT')
    o.append('  MOT 块: ' + ' '.join(chk[i:i+200].split())[:170])

a = io.open(os.path.join(REPO, 'common', 'bookmarks', '3_The_Traveler.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'common', 'bookmarks', '3_The_Traveler.txt'), 'rb').read()
o.append(f'双副本一致: {a == b}')
print('\n'.join(o))

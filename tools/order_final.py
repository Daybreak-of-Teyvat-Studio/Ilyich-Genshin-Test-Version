# -*- coding: utf-8 -*-
"""1) 大国排成目标顺序；2) 全部小国条目补 version = base_game（双副本）"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
WANT8 = ['MOT', 'LYY', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE']
MINORS = ['RAG', 'ANR', 'DRA', 'GUN', 'FAV', 'LAW', 'DVA', 'SPI', 'SAN', 'ASA', 'TSU', 'VAN',
          'NCE', 'NCP', 'NFF', 'NMN', 'NPS', 'NSC', 'ABY', 'PRI', 'HIL']
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

def tag_span(t, tag):
    m = re.search(r'(?m)^[ \t]*"?' + tag + r'"?\s*=\s*\{', t)
    if not m: return None
    bs = t.index('{', m.start())
    be = close_brace(t, bs)
    ls = t.rfind('\n', 0, m.start()) + 1
    return (ls, be)

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'common', 'bookmarks', '3_The_Traveler.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')

    # 1) 大国重排
    spans = []
    blocks = {}
    for tag in WANT8:
        sp = tag_span(t, tag)
        if not sp:
            o.append(f'{label}: 缺 {tag}')
            continue
        spans.append(sp)
        blocks[tag] = t[sp[0]:sp[1]].rstrip()
    if len(blocks) == 8:
        s0 = min(x[0] for x in spans)
        e0 = max(x[1] for x in spans)
        t = t[:s0] + '\r\n\r\n'.join(blocks[tag] for tag in WANT8) + '\r\n\r\n' + t[e0:]

    # 2) 小国补 version
    nv = 0
    for tag in MINORS:
        sp = tag_span(t, tag)
        if not sp:
            continue
        blk = t[sp[0]:sp[1]]
        if re.search(r'(?m)^\s*version\s*=', blk):
            continue
        blk2, nn = re.subn(r'(?m)^([ \t]*)#[ \t]*version[ \t]*=[^\r\n]*',
                           r'\g<1>version = base_game', blk, count=1)
        if nn == 0:
            blk2, nn = re.subn(r'(?m)^([ \t]*)ideology\s*=[^\r\n]*',
                               r'\g<0>\r\n\g<1>version = base_game', blk, count=1)
        if nn == 0:
            blk2, nn = re.subn(r'(?m)^([ \t]*)minor\s*=\s*yes[^\r\n]*',
                               r'\g<0>\r\n\g<1>version = base_game', blk, count=1)
        if nn:
            t = t[:sp[0]] + blk2 + t[sp[1]:]
            nv += 1
    io.open(fp, 'wb').write(t.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    seq = re.findall(r'(?m)^[ \t]*([A-Z]{3})\s*=\s*\{', chk)
    o.append(f'{label}: 大国顺序={seq[:8]}, version总数={chk.count("version = base_game")}, 补小国 {nv}, 括号 {chk.count("{")}=={chk.count("}")}')

a = io.open(os.path.join(REPO, 'common', 'bookmarks', '3_The_Traveler.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'common', 'bookmarks', '3_The_Traveler.txt'), 'rb').read()
o.append(f'双副本一致: {a == b}')
print('\n'.join(o))

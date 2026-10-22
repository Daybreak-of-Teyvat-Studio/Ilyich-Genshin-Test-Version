# -*- coding: utf-8 -*-
"""bug2 小国段重建：8 势力的小国（仅开局有地+有专属树）→ 深渊、天理、丘丘部落联盟"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
rel = os.path.join('common', 'bookmarks', '3_The_Traveler.txt')

GROUPS = [
    ('#蒙德', ['RAG', 'ANR', 'DRA', 'GUN', 'FAV', 'LAW', 'DVA', 'SPI']),
    ('#稻妻', ['SAN', 'ASA', 'TSU']),
    ('#须弥', ['VAN']),
    ('#纳塔', ['NCE', 'NCP', 'NFF', 'NMN', 'NPS', 'NSC']),
    ('#收束', ['ABY', 'PRI', 'HIL']),
]
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

def tag_block(t, tag):
    m = re.search(r'(?m)^[ \t]*"' + tag + r'"\s*=\s*\{', t)
    if not m:
        return None
    bs = t.index('{', m.start())
    be = close_brace(t, bs)
    return t[m.start():be]

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, rel)
    t = rd(fp)
    # 收集所有现有入口
    existing = {}
    for m in re.finditer(r'(?m)^[ \t]*"([A-Z]{3})"\s*=\s*\{', t):
        tag = m.group(1)
        b = tag_block(t, tag)
        if b:
            existing[tag] = b
    # 段起点 #mini
    i0 = t.find('#mini')
    if i0 < 0:
        o.append(f'{label}: 未找到 #mini ✗')
        continue
    # 段尾 = 最后一个 \t} 之前
    tail_start = t.rfind('\n\t}')
    if tail_start < i0:
        o.append(f'{label}: 尾定位失败 ✗')
        continue
    tail = t[tail_start:]

    parts = ['#mini']
    for gname, tags in GROUPS:
        parts.append('')
        parts.append(gname)
        if gname == '#收束':
            parts.append('')
        for tag in tags:
            if tag in existing:
                b = existing[tag]
                # 保持原缩进（2 tab 起）
                parts.append(b.rstrip())
            else:
                parts.append(f'\t\t"{tag}" = {{')
                parts.append('\t\t\tminor = yes')
                parts.append('\t\t}')
    newsec = '\r\n'.join(parts) + '\r\n'
    t2 = t[:i0] + newsec + tail
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    chk = rd(fp)
    seq = re.findall(r'(?m)^[ \t]*"([A-Z]{3})"\s*=\s*\{', chk)
    o.append(f'{label}: tag 序列={seq}')
    o.append(f'   括号 {chk.count("{")}=={chk.count("}")}, {len(chk)}B')

a = io.open(os.path.join(REPO, rel), 'rb').read()
b = io.open(os.path.join(DEPL, rel), 'rb').read()
o.append(f'双副本一致: {a == b}')
print('\n'.join(o))

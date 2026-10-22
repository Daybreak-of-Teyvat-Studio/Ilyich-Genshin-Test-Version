# -*- coding: utf-8 -*-
"""1) 书签顺序回退到原始；2) 查八个大国的国家定义文件（major/interesting 相关字段）"""
import os, io, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
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

# ---- 1) 书签前四恢复原始顺序 MOT,LYY,FON,NAT,NDK,SNE,INA,SUM（整体 8 块重排）----
ORIG = ['MOT', 'LYY', 'FON', 'NAT', 'NDK', 'SNE', 'INA', 'SUM']
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'common', 'bookmarks', '3_The_Traveler.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    blocks = {}
    spans = []
    for tag in ORIG:
        m = re.search(r'(?m)^[ \t]*"?' + tag + r'"?\s*=\s*\{', t)
        if not m:
            o.append(f'{label}: 缺 {tag}')
            continue
        bs = t.index('{', m.start())
        be = close_brace(t, bs)
        ls = t.rfind('\n', 0, m.start()) + 1
        blocks[tag] = t[ls:be].rstrip()
        spans.append((ls, be))
    if len(blocks) == 8:
        s0 = min(x[0] for x in spans)
        e0 = max(x[1] for x in spans)
        new = '\r\n\r\n'.join(blocks[tag] for tag in ORIG) + '\r\n\r\n'
        t = t[:s0] + new + t[e0:]
        io.open(fp, 'wb').write(t.encode('utf-8'))
        chk = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        seq = re.findall(r'(?m)^[ \t]*([A-Z]{3})\s*=\s*\{', chk)
        o.append(f'{label} 前 8 = {seq[:8]}, 括号 {chk.count("{")}=={chk.count("}")}')

# ---- 2) 查国家定义文件里的 major/interesting 字段 ----
o.append('')
o.append('===== common/countries 各文件首块内容（八大国） =====')
cd = os.path.join(REPO, 'common', 'countries')
name2tag = {'Mondstadt.txt': 'MOT', 'Liyue.txt': 'LYY', 'Inazuma.txt': 'INA', 'Sumeru.txt': 'SUM',
            'Fontaine.txt': 'FON', 'Natlan.txt': 'NAT', 'NDK.txt': 'NDK', 'Snezhnaya.txt': 'SNE'}
for f, tag in name2tag.items():
    fp = os.path.join(cd, f)
    if not os.path.exists(fp):
        o.append(f'  {f}: 不存在')
        continue
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'(?m)^\s*' + tag + r'\s*=\s*\{', t)
    body = ''
    if m:
        bs = t.index('{', m.start())
        be = close_brace(t, bs)
        body = ' '.join(t[bs:be].split())[:260]
    o.append(f'  {f}: {"存在" if m else "无 " + tag + " 块"} | {body}')
    for kw in ('major', 'interesting', 'priority'):
        if re.search(r'(?i)' + kw, t):
            mm = re.search(r'(?i)([^\n]*' + kw + r'[^\n]*)', t)
            o.append(f'     含 {kw}: {mm.group(1).strip()[:100]}')

a = io.open(os.path.join(REPO, 'common', 'bookmarks', '3_The_Traveler.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'common', 'bookmarks', '3_The_Traveler.txt'), 'rb').read()
o.append(f'bookmark 双副本一致: {a == b}')
print('\n'.join(o))

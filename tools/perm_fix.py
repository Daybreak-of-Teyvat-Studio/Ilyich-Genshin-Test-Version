# -*- coding: utf-8 -*-
"""1) 回退 filters 配对；2) 按观测到的置换反推，把前四国顺序改为 INA,MOT,SUM,LYY"""
import os, io, re, sys, shutil, subprocess
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.backups\ui_20261017_000603'
o = []

r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
if r.stdout.strip() != '0':
    print('hoi4 运行中，跳过')
    sys.exit(0)

# 1a) gui 恢复原版
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    shutil.copy2(os.path.join(BK, f'{label}_setup.gui'),
                 os.path.join(root, 'interface', 'frontendgamesetupview.gui'))
    o.append(f'{label} gui 回退: {os.path.getsize(os.path.join(root, "interface", "frontendgamesetupview.gui"))}B')
# 1b) bookmark filters 回注释
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'common', 'bookmarks', '3_The_Traveler.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    t2, n = re.subn(r'(?m)^\t\tfilters\s*=\s*\{\s*new_content\s+continent\s*\}',
                    '\t\t# filters = { new_content continent }', t)
    io.open(fp, 'wb').write(t2.encode('utf-8'))
    o.append(f'{label} bookmark filters 回注释: {n}')

# 2) 前四国重排：MOT,LYY,INA,SUM → INA,MOT,SUM,LYY（反推自 显示=LYY,SUM,MOT,INA）
ORDER4 = ['INA', 'MOT', 'SUM', 'LYY']

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
    # 拆出 ROW1/ROW2 之间的前 8 个块
    blocks = {}
    spans = []
    for tag in ('MOT', 'LYY', 'INA', 'SUM', 'FON', 'NAT', 'NDK', 'SNE'):
        m = re.search(r'(?m)^[ \t]*"?' + tag + r'"?\s*=\s*\{', t)
        if not m:
            o.append(f'{label}: 缺 {tag} ✗')
            continue
        bs = t.index('{', m.start())
        be = close_brace(t, bs)
        ls = t.rfind('\n', 0, m.start()) + 1
        blocks[tag] = t[ls:be]
        spans.append((ls, be))
    if len(blocks) != 8:
        continue
    start = spans[0][0]
    end = spans[1][1] if False else max(s for _, s in spans[:8])
    # 用前四个块的最小起止：前 4 个块 = 第 1-4 个 span
    sp4 = sorted(spans, key=lambda x: x[0])[:4]
    s0, e0 = sp4[0][0], sp4[-1][1]
    new4 = '\r\n\r\n'.join(blocks[tag].rstrip() for tag in ORDER4) + '\r\n\r\n'
    t = t[:s0] + new4 + t[e0:]
    io.open(fp, 'wb').write(t.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    seq = re.findall(r'(?m)^[ \t]*([A-Z]{3})\s*=\s*\{', chk)
    o.append(f'{label} 前 8 = {seq[:8]}')

for rel in (os.path.join('interface', 'frontendgamesetupview.gui'), os.path.join('common', 'bookmarks', '3_The_Traveler.txt')):
    a = io.open(os.path.join(REPO, rel), 'rb').read()
    b = io.open(os.path.join(DEPL, rel), 'rb').read()
    o.append(f'{rel}: 双副本一致={a == b}')
print('\n'.join(o))

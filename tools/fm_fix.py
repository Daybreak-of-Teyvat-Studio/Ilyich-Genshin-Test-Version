# -*- coding: utf-8 -*-
"""frontendmainview.gui 补 7 个缺失元素（按父容器插入，含容器去重）+ 跑游戏复验"""
import os, io, re, sys, shutil, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
o = []

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig')

def blocks(t):
    """返回 [(start, end, closing_index, name_or_None)]（按 '{' 堆栈）"""
    res = []
    stack = []
    for i, ch in enumerate(t):
        if ch == '{':
            stack.append(i)
        elif ch == '}':
            if stack:
                s = stack.pop()
                seg = t[s:i]
                m = re.match(r'\s*([A-Za-z_]+)\s*=\s*\{', t[max(0, s - 40):s + 1])
                nm = None
                m2 = re.search(r'name\s*=\s*"([^"]+)"', t[s:i])
                if m2:
                    nm = m2.group(1)
                res.append((s, i + 1, nm))
    return res

def block_of(t, blks, name):
    best = None
    for s, e, nm in blks:
        if nm == name:
            if best is None or (e - s) < (best[1] - best[0]):
                best = (s, e)
    return best

def parent_of(t, blks, s, e):
    best = None
    for s2, e2, nm in blks:
        if s2 < s and e2 >= e and nm:
            if best is None or (s2 > best[0]):
                best = (s2, e2, nm)
    return best

# ---- 取出原版 7 个缺失元素及其父 ----
vpath = os.path.join(V, 'interface', 'frontendmainview.gui')
tv = rd(vpath)
vb = blocks(tv)
gtext = rd(os.path.join(G, 'interface', 'frontendmainview.gui'))
gnames = set(re.findall(r'name\s*=\s*"([^"]+)"', gtext))
vnames = set(re.findall(r'name\s*=\s*"([^"]+)"', tv))
missing = sorted(vnames - gnames)
o.append(f'缺失元素: {missing}')

# 建每个缺失元素：(名字, 文本, 顶层父名)
items = []
for nm in missing:
    r = block_of(tv, vb, nm)
    if not r:
        o.append(f'  ⚠ 定位不到 {nm}')
        continue
    s, e = r
    # 找应插入的父（沿父链向上，直到父不是缺失元素）
    parent = None
    cur = (s, e)
    while True:
        p = parent_of(tv, vb, cur[0], cur[1])
        if not p:
            break
        if p[2] in missing:
            cur = (p[0], p[1])
            continue
        parent = p[2]
        break
    if parent is None:
        o.append(f'  ⚠ {nm} 找不到非缺失父容器')
        continue
    items.append((nm, tv[s:e], parent))
o.append(f'待插入: {[(n, p) for n, _, p in items]}')

# ---- 插入到 mod 文件 ----
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'interface', 'frontendmainview.gui')
    t = rd(fp)
    shutil.copy2(fp, os.path.join(REPO, '.backups', f'ui_{label}_fm.gui') if False else fp + '.bak_tmp')
    ok = 0
    for nm, blk, parent in items:
        blks2 = blocks(t)
        pr = block_of(t, blks2, parent)
        if not pr:
            o.append(f'  ⚠ {label} 父 {parent} 不在 mod 文件（元素 {nm}）')
            continue
        ps, pe = pr
        ins = t.rfind('\n', 0, pe - 1) + 1
        t = t[:ins] + blk.rstrip() + '\n' + t[ins:]
        ok += 1
    io.open(fp, 'wb').write(t.encode('utf-8'))
    chk = rd(fp)
    got = set(re.findall(r'name\s*=\s*"([^"]+)"', chk))
    o.append(f'  {label}: 插入 {ok}/{len(items)}, 现含缺失元素={[m for m in missing if m in got]}, 括号 {chk.count("{")}=={chk.count("}")}')
    os.remove(fp + '.bak_tmp')

a = io.open(os.path.join(G, 'interface', 'frontendmainview.gui'), 'rb').read()
b = io.open(os.path.join(DEPL, 'interface', 'frontendmainview.gui'), 'rb').read()
o.append(f'双副本一致: {a == b}')

# ---- 跑游戏复验 ----
o.append('')
o.append('===== 跑游戏复验 =====')
subprocess.run(['powershell', '-NoProfile', '-Command',
                "$p = Start-Process -FilePath 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV\\hoi4.exe' "
                "-ArgumentList '-debug' -WorkingDirectory 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV' -PassThru; "
                "Start-Sleep -Seconds 95; if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }"])
time.sleep(3)
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
l2 = t.splitlines()
for k in ('Could not find sprite type', 'Could not find "', 'MAP_ERROR', 'not within specified state', 'coastal but has no port'):
    o.append(f'  [{len([1 for l in l2 if k in l])}] {k}')
for l in l2:
    if 'Could not find' in l:
        o.append('    ' + l.strip()[:180])
io.open(os.path.join(REPO, 'tools', 'fm_fix_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

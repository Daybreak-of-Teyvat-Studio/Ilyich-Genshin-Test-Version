# -*- coding: utf-8 -*-
"""诊断主菜单左下角 DLC 图标少一个：原版 vs mod（只读，不动本地 mod）"""
import os, io, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\dlc_recon_out.txt'
o = []

# 1) dlc052 目录内容
d52 = os.path.join(V, 'dlc', 'dlc052_thunder_at_our_gates')
o.append('===== dlc052 目录 =====')
if os.path.isdir(d52):
    for dp, dn, fn in os.walk(d52):
        for f in fn:
            o.append('  ' + os.path.relpath(os.path.join(dp, f), d52) + f'  {os.path.getsize(os.path.join(dp, f))}B')
else:
    o.append('  不存在')

# 2) 读 dlc052 的元数据（找 icon/picture）
o.append('')
o.append('===== dlc052 元数据 =====')
for fp in glob.glob(os.path.join(d52, '**', '*'), recursive=True):
    if os.path.isfile(fp) and fp.lower().endswith(('.txt', '.dlc', '.json')):
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        o.append(f'--- {os.path.relpath(fp, d52)} ---')
        for l in t.splitlines()[:40]:
            o.append('  ' + l.strip()[:160])

# 3) 原版 interface 里 dlc 图标 sprite 定义（含 dlc051/052/053）
o.append('')
o.append('===== 原版 interface 中 dlc 图标 sprite（名字 + 贴图） =====')
for fp in glob.glob(os.path.join(V, 'interface', '**', '*.gfx'), recursive=True):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for m in re.finditer(r'spriteType\s*=\s*\{([^}]*)\}', t, re.S):
        b = m.group(1)
        if re.search(r'dlc0\d\d', b):
            nm = re.search(r'name\s*=\s*"([^"]+)"', b)
            tx = re.search(r'texturefile\s*=\s*"([^"]+)"', b)
            o.append(f'  [{os.path.relpath(fp, V)}] {nm.group(1) if nm else "?"} → {tx.group(1) if tx else "?"}')

# 4) mod 里是否有同名 sprite/贴图
o.append('')
o.append('===== mod 侧对照（同名 sprite 是否存在 + 贴图是否存在） =====')
vl = {}
for fp in glob.glob(os.path.join(V, 'interface', '**', '*.gfx'), recursive=True):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for m in re.finditer(r'spriteType\s*=\s*\{([^}]*)\}', t, re.S):
        b = m.group(1)
        nm = re.search(r'name\s*=\s*"([^"]+)"', b)
        tx = re.search(r'texturefile\s*=\s*"([^"]+)"', b)
        if nm and re.search(r'dlc0\d\d', b):
            vl[nm.group(1)] = (os.path.relpath(fp, V), tx.group(1) if tx else '?')
mg = set()
for fp in glob.glob(os.path.join(G, 'interface', '**', '*.gfx'), recursive=True):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    mg |= set(re.findall(r'name\s*=\s*"([^"]+)"', t))
for nm, (src, tx) in sorted(vl.items()):
    tex_mod = os.path.exists(os.path.join(G, tx.replace('//', '/').lstrip('/')))
    tex_van = os.path.exists(os.path.join(V, tx.replace('//', '/').lstrip('/')))
    o.append(f'  {nm}: mod 有 sprite={"是" if nm in mg else "【否】"}, 贴图 mod={tex_mod} 原版={tex_van} ({tx})')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))

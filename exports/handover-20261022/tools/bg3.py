# -*- coding: utf-8 -*-
import os, io, re, sys, glob, struct
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
o = []

def dds_info(fp):
    h = io.open(fp, 'rb').read(30)
    if h[:4] != b'DDS ':
        return '非DDS'
    hh, ww = struct.unpack('<II', h[12:20])
    return f'{ww}x{hh}'

o.append('===== frontendmainviewbg.gfx 对比 =====')
for label, root in [('mod', G), ('原版', V)]:
    for fn in ('frontendmainviewbg.gfx', 'DOT_frontendmainviewbg.gfx'):
        fp = os.path.join(root, 'interface', fn)
        if not os.path.exists(fp):
            continue
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        sp = re.findall(r'spriteType\s*=\s*\{([^}]*)\}', t, re.S)
        o.append(f'--- {label} {fn}: {len(t)}B, {len(sp)} sprites ---')
        for b in sp[:12]:
            nm = re.search(r'name\s*=\s*"([^"]+)"', b)
            tx = re.search(r'texturefile\s*=\s*"([^"]+)"', b)
            o.append(f'   {nm.group(1) if nm else "?"} -> {tx.group(1) if tx else "?"}')
        o.append('')

o.append('===== loadingscreens 文件对照 =====')
for label, root in [('mod', G), ('原版', V)]:
    d = os.path.join(root, 'gfx', 'loadingscreens')
    fs = sorted(os.listdir(d)) if os.path.isdir(d) else []
    o.append(f'[{label}] {len(fs)} 个:')
    for f in fs[:45]:
        fp = os.path.join(d, f)
        o.append(f'   {f}  {os.path.getsize(fp)}B  {dds_info(fp)}')
    o.append('')
print('\n'.join(o))

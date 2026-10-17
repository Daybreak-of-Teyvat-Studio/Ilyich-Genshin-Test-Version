# -*- coding: utf-8 -*-
import io, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
exe = r'F:\Steam\steamapps\common\Hearts of Iron IV\hoi4.exe'
raw = open(exe, 'rb').read()
o = []
# 找 -nudge / nudge 相关命令行字符串
for pat in (rb'-nudge', rb'nudge', rb'map_editor', rb'maptool', rb'-editor'):
    idxs = [m.start() for m in re.finditer(re.escape(pat), raw, re.I)][:6]
    o.append(f'模式 {pat!r}: {len(idxs)} 处')
    for i in idxs[:6]:
        seg = raw[max(0, i - 60):i + 80]
        # 提取可见字符串
        vis = re.findall(rb'[\x20-\x7e]{4,}', seg)
        o.append(f'    {b" | ".join(vis)[:200]}')
print('\n'.join(o))
io.open(r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\nudgeflag_out.txt', 'w', encoding='utf-8').write('\n'.join(o))

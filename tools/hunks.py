# -*- coding: utf-8 -*-
import os, io, re, sys, difflib
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = os.path.join(REPO, 'tools', 'hunks_out.txt')
o = []

def norm(p):
    return io.open(p, 'rb').read().decode('utf-8-sig', errors='replace').replace('\r\n', '\n').split('\n')

for rel in ('interface/core.gfx', 'interface/frontendmainview.gfx',
            'interface/frontendmainview.gui', 'interface/frontendgamesetupview.gui'):
    a = norm(os.path.join(G, rel.replace('/', os.sep)))
    b = norm(os.path.join(V, rel.replace('/', os.sep)))
    o.append(f'########## {rel} ##########')
    d = list(difflib.unified_diff(a, b, 'mod', 'vanilla', lineterm='', n=0))
    # 分组输出：原版多出的（+）与 mod 独有（-）
    o.append('--- 原版多出（需补进 mod） ---')
    ctx = []
    for l in d:
        if l.startswith('@@'):
            ctx = [l]
            o.append('  ' + l)
        elif l.startswith('+') and not l.startswith('+++'):
            o.append('    ' + l[1:][:165])
        elif l.startswith('-') and not l.startswith('---'):
            o.append('  ~mod独有~ ' + l[1:][:165])
    o.append('')
    o.append(f'（{rel} 差异行: 原版多 {sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))}, mod独有 {sum(1 for l in d if l.startswith("-") and not l.startswith("---"))}）')
    o.append('')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print(f'写入 {OUT}，{len(o)} 行')
print('\n'.join(o[:120]))

# -*- coding: utf-8 -*-
import os, io, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\vp_fmt_out.txt'
o = []

def scan(label, root):
    sd = os.path.join(root, 'history', 'states')
    if not os.path.isdir(sd):
        o.append(f'{label}: 无 states 目录')
        return
    multi_pair = []      # 一个块里多个 pair
    multi_block = []     # 多个 victory_points 块
    single = 0
    ex_multi_pair = []
    for f in os.listdir(sd):
        if not f.endswith('.txt'):
            continue
        t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
        blocks = re.findall(r'victory_points\s*=\s*\{([^}]*)\}', t)
        if not blocks:
            continue
        if len(blocks) > 1:
            multi_block.append((f, blocks))
        for b in blocks:
            toks = b.split()
            if len(toks) > 2:
                multi_pair.append((f, toks))
                if len(ex_multi_pair) < 6:
                    ex_multi_pair.append((f, ' '.join(toks)[:100]))
            else:
                single += 1
    o.append(f'===== {label} =====')
    o.append(f'  单对块 {single} 个；多对块 {len(multi_pair)} 个；多块州 {len(multi_block)} 个')
    for f, s in ex_multi_pair:
        o.append(f'  多对示例: {f}: {s}')
    for f, blocks in multi_block[:5]:
        o.append(f'  多块示例: {f}: {blocks}')

scan('Gamma(当前)', G)
scan('Beta', B)
scan('原版', V)

# 352 的旧键内容
o.append('')
o.append('===== VICTORY_POINTS_352 在旧 loc 文件里的内容 =====')
import glob
for fp in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    for l in t.splitlines():
        if 'VICTORY_POINTS_352:' in l or ('352' in l and 'VICTORY_POINTS' in l):
            o.append(f'  {os.path.basename(fp)}: {l.strip()[:120]}')

# 蒙德城相关：检查 466 州的当前 VP 块原文 + 城文件里 466 州有没有别的 VP 引用
o.append('')
o.append('===== 州466 文件 victory_points 上下文 =====')
t = io.open(os.path.join(G, 'history', 'states', '466-State_466.txt'), 'rb').read().decode('utf-8-sig', errors='replace')
i = t.find('victory_points')
o.append('  ' + repr(t[max(0,i-220):i+120]))

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
